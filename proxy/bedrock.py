import json
import ssl
import time
from pathlib import Path

import aiohttp
from aiohttp import web

from .logger import CallLogger
from .sse_parser import accumulate_response
from .port_utils import find_available_port


BEDROCK_HOST = "bedrock-runtime.us-east-1.amazonaws.com"


class BedrockProxyServer:
    def __init__(self, port: int = 8080, log_dir: Path = Path("logs"), region: str = "us-east-1"):
        self.port = port
        self.log_dir = log_dir
        self.region = region
        self.upstream_base = f"https://bedrock-runtime.{region}.amazonaws.com"
        self.logger = CallLogger(log_dir)
        self.current_session_id = "default"
        self.call_counters: dict[str, int] = {}
        self._client_session: aiohttp.ClientSession | None = None

    def _next_call_index(self) -> int:
        sid = self.current_session_id
        self.call_counters.setdefault(sid, 0)
        self.call_counters[sid] += 1
        return self.call_counters[sid]

    async def _get_client(self) -> aiohttp.ClientSession:
        if self._client_session is None or self._client_session.closed:
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
            conn = aiohttp.TCPConnector(ssl=ssl_ctx)
            self._client_session = aiohttp.ClientSession(connector=conn)
        return self._client_session

    async def handle_control_session(self, request: web.Request) -> web.Response:
        data = await request.json()
        self.current_session_id = data.get("session_id", "default")
        self.call_counters.setdefault(self.current_session_id, 0)
        return web.json_response({"status": "ok", "session_id": self.current_session_id})

    async def handle_control_status(self, request: web.Request) -> web.Response:
        return web.json_response({
            "status": "running",
            "session_id": self.current_session_id,
            "call_count": self.call_counters.get(self.current_session_id, 0),
        })

    async def handle_invoke(self, request: web.Request) -> web.StreamResponse:
        body = await request.read()
        request_data = json.loads(body)
        start_time = time.time()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())

        model_id = request.match_info.get("model_id", "unknown")

        # Extract session ID from custom header if present
        session_id = request.headers.get("X-Session-ID", self.current_session_id)

        headers = {}
        for key, value in request.headers.items():
            lower = key.lower()
            if lower in ("host", "content-length", "transfer-encoding"):
                continue
            headers[key] = value
        headers["Host"] = f"bedrock-runtime.{self.region}.amazonaws.com"

        client = await self._get_client()
        target_url = f"{self.upstream_base}{request.path}"

        is_streaming = "invoke-with-response-stream" in request.path

        if is_streaming:
            return await self._handle_streaming(
                client, target_url, headers, body, request_data, request, model_id, start_time, timestamp, session_id
            )
        else:
            return await self._handle_non_streaming(
                client, target_url, headers, body, request_data, model_id, start_time, timestamp, session_id
            )

    async def _handle_streaming(
        self, client, target_url, headers, body, request_data, request, model_id, start_time, timestamp, session_id
    ) -> web.StreamResponse:
        async with client.post(target_url, headers=headers, data=body) as upstream:
            response = web.StreamResponse(status=upstream.status)
            content_type = upstream.headers.get("content-type", "application/vnd.amazon.eventstream")
            response.content_type = content_type
            for key in ("x-amzn-requestid", "x-amzn-bedrock-invocation-latency"):
                if key in upstream.headers:
                    response.headers[key] = upstream.headers[key]
            await response.prepare(request)

            accumulated_chunks: list[bytes] = []

            async for chunk in upstream.content.iter_any():
                await response.write(chunk)
                accumulated_chunks.append(chunk)

            await response.write_eof()

        latency_ms = (time.time() - start_time) * 1000

        try:
            response_data = self._parse_bedrock_stream(accumulated_chunks)
        except Exception:
            response_data = {"_parse_error": True, "_raw_size": sum(len(c) for c in accumulated_chunks)}

        # Use session-specific counter
        self.call_counters.setdefault(session_id, 0)
        self.call_counters[session_id] += 1
        call_index = self.call_counters[session_id]

        await self.logger.log_call(
            session_id,
            call_index,
            self._normalize_request(request_data, model_id),
            response_data,
            {"latency_ms": latency_ms, "timestamp": timestamp},
        )
        return response

    async def _handle_non_streaming(
        self, client, target_url, headers, body, request_data, model_id, start_time, timestamp, session_id
    ) -> web.Response:
        async with client.post(target_url, headers=headers, data=body) as upstream:
            response_body = await upstream.read()
            latency_ms = (time.time() - start_time) * 1000

            try:
                response_data = json.loads(response_body)
            except json.JSONDecodeError:
                response_data = {}

            # Use session-specific counter
            self.call_counters.setdefault(session_id, 0)
            self.call_counters[session_id] += 1
            call_index = self.call_counters[session_id]

            await self.logger.log_call(
                session_id,
                call_index,
                self._normalize_request(request_data, model_id),
                response_data,
                {"latency_ms": latency_ms, "timestamp": timestamp},
            )

            resp_headers = {}
            for key in ("x-amzn-requestid", "content-type"):
                if key in upstream.headers:
                    resp_headers[key] = upstream.headers[key]

            return web.Response(
                status=upstream.status,
                body=response_body,
                headers=resp_headers,
            )

    def _parse_bedrock_stream(self, chunks: list[bytes]) -> dict:
        import base64

        raw = b"".join(chunks)
        events = self._decode_eventstream(raw)

        if events:
            reconstructed = accumulate_response(events)
            return reconstructed

        return {"_raw_size": len(raw), "_event_count": 0}

    def _decode_eventstream(self, raw: bytes) -> list[dict]:
        import base64
        import struct

        events = []
        offset = 0
        while offset + 12 <= len(raw):
            # AWS event stream binary frame:
            # [4 bytes total_length] [4 bytes headers_length] [4 bytes prelude_crc]
            # [headers] [payload] [4 bytes message_crc]
            total_length = struct.unpack("!I", raw[offset:offset+4])[0]
            if total_length < 16 or offset + total_length > len(raw):
                break
            headers_length = struct.unpack("!I", raw[offset+4:offset+8])[0]

            # payload starts after prelude (12 bytes) + headers
            payload_start = offset + 12 + headers_length
            # payload ends before message CRC (4 bytes)
            payload_end = offset + total_length - 4
            payload = raw[payload_start:payload_end]

            if payload:
                try:
                    parsed = json.loads(payload)
                    # Bedrock wraps the actual event in {"bytes": "<base64>"}
                    if "bytes" in parsed:
                        decoded = base64.b64decode(parsed["bytes"])
                        try:
                            event = json.loads(decoded)
                            events.append(event)
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            pass
                    elif "type" in parsed:
                        events.append(parsed)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass

            offset += total_length
        return events

    def _normalize_request(self, request_data: dict, model_id: str) -> dict:
        normalized = dict(request_data)
        normalized.setdefault("model", model_id)
        return normalized

    async def handle_catch_all(self, request: web.Request) -> web.Response:
        body = await request.read()
        headers = {
            k: v for k, v in request.headers.items()
            if k.lower() not in ("host", "content-length", "transfer-encoding")
        }
        headers["Host"] = f"bedrock-runtime.{self.region}.amazonaws.com"

        client = await self._get_client()
        target_url = f"{self.upstream_base}{request.path}"

        method = getattr(client, request.method.lower())
        async with method(target_url, headers=headers, data=body if body else None) as upstream:
            resp_body = await upstream.read()
            return web.Response(
                status=upstream.status,
                body=resp_body,
                content_type=upstream.headers.get("content-type", "application/json"),
            )

    async def on_shutdown(self, app: web.Application):
        if self._client_session and not self._client_session.closed:
            await self._client_session.close()

    def create_app(self) -> web.Application:
        app = web.Application()
        app.router.add_post("/control/set-session", self.handle_control_session)
        app.router.add_get("/control/status", self.handle_control_status)
        app.router.add_post("/model/{model_id}/invoke", self.handle_invoke)
        app.router.add_post("/model/{model_id}/invoke-with-response-stream", self.handle_invoke)
        app.router.add_route("*", "/{path:.*}", self.handle_catch_all)
        app.on_shutdown.append(self.on_shutdown)
        return app

    async def start(self):
        app = self.create_app()
        runner = web.AppRunner(app)
        await runner.setup()

        # Try to find an available port starting from the requested port
        available_port = find_available_port(self.port)
        if available_port is None:
            raise RuntimeError(f"Could not find available port starting from {self.port}")

        if available_port != self.port:
            print(f"Port {self.port} is in use, using port {available_port} instead")
            self.port = available_port

        site = web.TCPSite(runner, "127.0.0.1", self.port)
        await site.start()
        return runner
