import json
import time
from pathlib import Path

import aiohttp
from aiohttp import web

from .logger import CallLogger
from .sse_parser import ReconstructedResponse, accumulate_response


class ProxyServer:
    def __init__(self, port: int = 8080, log_dir: Path = Path("logs"), api_url: str = "https://api.anthropic.com"):
        self.port = port
        self.log_dir = log_dir
        self.api_url = api_url
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
            self._client_session = aiohttp.ClientSession()
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

    async def handle_messages(self, request: web.Request) -> web.Response | web.StreamResponse:
        body = await request.read()
        request_data = json.loads(body)
        is_streaming = request_data.get("stream", False)
        start_time = time.time()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())

        headers = {}
        for key, value in request.headers.items():
            lower = key.lower()
            if lower in ("host", "content-length", "transfer-encoding"):
                continue
            headers[key] = value

        client = await self._get_client()
        target_url = f"{self.api_url}{request.path}"

        if is_streaming:
            return await self._handle_streaming(client, target_url, headers, body, request_data, request, start_time, timestamp)
        else:
            return await self._handle_non_streaming(client, target_url, headers, body, request_data, start_time, timestamp)

    async def _handle_streaming(
        self, client, target_url, headers, body, request_data, request, start_time, timestamp
    ) -> web.StreamResponse:
        async with client.post(target_url, headers=headers, data=body) as upstream:
            response = web.StreamResponse(status=upstream.status)
            response.content_type = "text/event-stream"
            response.headers["Cache-Control"] = "no-cache"
            for key in ("x-request-id", "request-id"):
                if key in upstream.headers:
                    response.headers[key] = upstream.headers[key]
            await response.prepare(request)

            accumulated_lines: list[str] = []
            buffer = b""

            async for chunk in upstream.content.iter_any():
                await response.write(chunk)
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    decoded = line.decode("utf-8", errors="replace").strip()
                    if decoded:
                        accumulated_lines.append(decoded)

            if buffer:
                decoded = buffer.decode("utf-8", errors="replace").strip()
                if decoded:
                    accumulated_lines.append(decoded)

            await response.write_eof()

        latency_ms = (time.time() - start_time) * 1000
        events = []
        for line in accumulated_lines:
            if line.startswith("data: "):
                payload = line[6:]
                if payload == "[DONE]":
                    continue
                try:
                    events.append(json.loads(payload))
                except json.JSONDecodeError:
                    pass

        reconstructed = accumulate_response(events)
        call_index = self._next_call_index()
        await self.logger.log_call(
            self.current_session_id,
            call_index,
            request_data,
            reconstructed,
            {"latency_ms": latency_ms, "timestamp": timestamp},
        )
        return response

    async def _handle_non_streaming(
        self, client, target_url, headers, body, request_data, start_time, timestamp
    ) -> web.Response:
        async with client.post(target_url, headers=headers, data=body) as upstream:
            response_body = await upstream.read()
            latency_ms = (time.time() - start_time) * 1000

            try:
                response_data = json.loads(response_body)
            except json.JSONDecodeError:
                response_data = {}

            call_index = self._next_call_index()
            await self.logger.log_call(
                self.current_session_id,
                call_index,
                request_data,
                response_data,
                {"latency_ms": latency_ms, "timestamp": timestamp},
            )

            resp_headers = {}
            for key in ("x-request-id", "request-id", "content-type"):
                if key in upstream.headers:
                    resp_headers[key] = upstream.headers[key]

            return web.Response(
                status=upstream.status,
                body=response_body,
                headers=resp_headers,
            )

    async def handle_catch_all(self, request: web.Request) -> web.Response:
        body = await request.read()
        headers = {
            k: v for k, v in request.headers.items()
            if k.lower() not in ("host", "content-length", "transfer-encoding")
        }
        client = await self._get_client()
        target_url = f"{self.api_url}{request.path}"

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
        app.router.add_post("/v1/messages", self.handle_messages)
        app.router.add_route("*", "/{path:.*}", self.handle_catch_all)
        app.on_shutdown.append(self.on_shutdown)
        return app

    async def start(self):
        app = self.create_app()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", self.port)
        await site.start()
        return runner
