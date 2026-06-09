import json
from pathlib import Path

from aiohttp import web


class VizServer:
    def __init__(self, log_dir: Path, port: int = 8090):
        self.log_dir = log_dir
        self.port = port
        self.static_dir = Path(__file__).parent / "static"

    def _load_session(self, session_dir: Path) -> dict:
        calls = []
        for call_file in sorted(session_dir.glob("call_*.json")):
            with open(call_file) as f:
                calls.append(json.load(f))
        return {
            "session_id": session_dir.name.replace("session_", ""),
            "calls": calls,
            "num_calls": len(calls),
            "total_cost": sum(c.get("cost", {}).get("total_cost", 0) for c in calls),
            "total_input_tokens": sum(c.get("tokens", {}).get("input_tokens", 0) for c in calls),
            "total_output_tokens": sum(c.get("tokens", {}).get("output_tokens", 0) for c in calls),
            "avg_latency_ms": (
                sum(c.get("performance", {}).get("latency_ms", 0) for c in calls) / len(calls)
                if calls else 0
            ),
            "model": calls[0].get("meta", {}).get("model", "unknown") if calls else "unknown",
        }

    async def handle_sessions(self, request: web.Request) -> web.Response:
        sessions = []
        if self.log_dir.exists():
            for session_dir in sorted(self.log_dir.iterdir()):
                if session_dir.is_dir() and session_dir.name.startswith("session_"):
                    summary = self._load_session(session_dir)
                    summary.pop("calls", None)
                    sessions.append(summary)
        return web.json_response(sessions)

    async def handle_session_detail(self, request: web.Request) -> web.Response:
        session_id = request.match_info["session_id"]
        session_dir = self.log_dir / f"session_{session_id}"
        if not session_dir.exists():
            return web.json_response({"error": "session not found"}, status=404)
        return web.json_response(self._load_session(session_dir))

    async def handle_call_detail(self, request: web.Request) -> web.Response:
        session_id = request.match_info["session_id"]
        call_index = int(request.match_info["index"])
        call_file = self.log_dir / f"session_{session_id}" / f"call_{call_index:03d}.json"
        if not call_file.exists():
            return web.json_response({"error": "call not found"}, status=404)
        with open(call_file) as f:
            return web.json_response(json.load(f))

    async def handle_summary(self, request: web.Request) -> web.Response:
        total_calls = 0
        total_cost = 0.0
        total_latency = 0.0
        total_input = 0
        total_output = 0
        total_cache_read = 0
        total_cache_write = 0
        tool_counts: dict[str, int] = {}

        if self.log_dir.exists():
            for session_dir in self.log_dir.iterdir():
                if not session_dir.is_dir() or not session_dir.name.startswith("session_"):
                    continue
                for call_file in session_dir.glob("call_*.json"):
                    with open(call_file) as f:
                        call = json.load(f)
                    total_calls += 1
                    total_cost += call.get("cost", {}).get("total_cost", 0)
                    total_latency += call.get("performance", {}).get("latency_ms", 0)
                    tokens = call.get("tokens", {})
                    total_input += tokens.get("input_tokens", 0)
                    total_output += tokens.get("output_tokens", 0)
                    total_cache_read += tokens.get("cache_read_input_tokens", 0)
                    total_cache_write += tokens.get("cache_creation_input_tokens", 0)
                    for tool in call.get("tools", []):
                        name = tool.get("name", "unknown")
                        tool_counts[name] = tool_counts.get(name, 0) + 1

        cache_total = total_input + total_cache_read + total_cache_write
        cache_efficiency = (total_cache_read / cache_total * 100) if cache_total > 0 else 0

        return web.json_response({
            "total_calls": total_calls,
            "total_cost": round(total_cost, 6),
            "avg_latency_ms": round(total_latency / total_calls, 1) if total_calls else 0,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cache_read_tokens": total_cache_read,
            "total_cache_write_tokens": total_cache_write,
            "cache_efficiency_pct": round(cache_efficiency, 2),
            "tool_frequency": dict(sorted(tool_counts.items(), key=lambda x: -x[1])),
        })

    async def handle_workspace(self, request: web.Request) -> web.Response:
        session_id = request.match_info["session_id"]
        workspace = self.log_dir / f"session_{session_id}" / "workspace"
        if not workspace.exists():
            return web.json_response({"tree": [], "files": {}})

        tree = []
        files = {}
        for f in sorted(workspace.rglob("*")):
            if f.is_file():
                rel = str(f.relative_to(workspace))
                tree.append(rel)
                if f.suffix in (".py", ".js", ".ts", ".html", ".css", ".json", ".md", ".txt", ".sh", ".c", ".h", ".toml", ".yaml", ".yml", ".cfg", ".ini"):
                    try:
                        content = f.read_text(errors="replace")
                        files[rel] = content[:5000]
                    except Exception:
                        files[rel] = "(unreadable)"

        return web.json_response({"tree": tree, "files": files})

    async def handle_index(self, request: web.Request) -> web.FileResponse:
        return web.FileResponse(self.static_dir / "index.html")

    def create_app(self) -> web.Application:
        app = web.Application()
        app.router.add_get("/", self.handle_index)
        app.router.add_get("/api/sessions", self.handle_sessions)
        app.router.add_get("/api/sessions/{session_id}", self.handle_session_detail)
        app.router.add_get("/api/sessions/{session_id}/calls/{index}", self.handle_call_detail)
        app.router.add_get("/api/sessions/{session_id}/workspace", self.handle_workspace)
        app.router.add_get("/api/summary", self.handle_summary)
        app.router.add_static("/static", self.static_dir)
        return app

    async def start(self):
        app = self.create_app()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", self.port)
        await site.start()
        return runner
