import json
import time
from pathlib import Path

import aiofiles

from .pricing import calculate_cost
from .sse_parser import ReconstructedResponse


class CallLogger:
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir

    async def log_call(
        self,
        session_id: str,
        call_index: int,
        request_data: dict,
        response: ReconstructedResponse | dict,
        metadata: dict,
    ) -> Path:
        if isinstance(response, ReconstructedResponse):
            entry = self._build_from_reconstructed(session_id, call_index, request_data, response, metadata)
        else:
            entry = self._build_from_dict(session_id, call_index, request_data, response, metadata)

        session_dir = self.log_dir / f"session_{session_id}"
        session_dir.mkdir(parents=True, exist_ok=True)
        filepath = session_dir / f"call_{call_index:03d}.json"

        async with aiofiles.open(filepath, "w") as f:
            await f.write(json.dumps(entry, indent=2, default=str))

        return filepath

    def _build_from_reconstructed(
        self, session_id: str, call_index: int, request_data: dict,
        response: ReconstructedResponse, metadata: dict,
    ) -> dict:
        tokens = {
            "input_tokens": response.usage.get("input_tokens", 0),
            "output_tokens": response.usage.get("output_tokens", 0),
            "cache_creation_input_tokens": response.usage.get("cache_creation_input_tokens", 0),
            "cache_read_input_tokens": response.usage.get("cache_read_input_tokens", 0),
        }
        model = response.model or request_data.get("model", "unknown")
        cost = calculate_cost(model, tokens)
        tools = self._extract_tools_from_blocks(response.content_blocks)
        messages = request_data.get("messages", [])

        return {
            "meta": {
                "timestamp": metadata.get("timestamp", time.strftime("%Y-%m-%dT%H:%M:%S.000Z")),
                "model": model,
                "session_id": session_id,
                "call_index": call_index,
                "max_tokens": request_data.get("max_tokens"),
                "temperature": request_data.get("temperature"),
                "system_prompt": self._extract_system(request_data),
            },
            "tokens": tokens,
            "cost": cost,
            "context": self._compute_context(tokens, messages),
            "tools": tools,
            "performance": {
                "latency_ms": round(metadata.get("latency_ms", 0), 1),
                "stop_reason": response.stop_reason,
            },
            "conversation": {
                "messages": messages,
                "assistant_response": response.assistant_text,
            },
        }

    def _build_from_dict(
        self, session_id: str, call_index: int, request_data: dict,
        response_data: dict, metadata: dict,
    ) -> dict:
        usage = response_data.get("usage", {})
        tokens = {
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
            "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
        }
        model = response_data.get("model", request_data.get("model", "unknown"))
        cost = calculate_cost(model, tokens)
        content = response_data.get("content", [])
        tools = self._extract_tools_from_blocks(content)
        assistant_text = "".join(
            block.get("text", "") for block in content if block.get("type") == "text"
        )
        messages = request_data.get("messages", [])

        return {
            "meta": {
                "timestamp": metadata.get("timestamp", time.strftime("%Y-%m-%dT%H:%M:%S.000Z")),
                "model": model,
                "session_id": session_id,
                "call_index": call_index,
                "max_tokens": request_data.get("max_tokens"),
                "temperature": request_data.get("temperature"),
                "system_prompt": self._extract_system(request_data),
            },
            "tokens": tokens,
            "cost": cost,
            "context": self._compute_context(tokens, messages),
            "tools": tools,
            "performance": {
                "latency_ms": round(metadata.get("latency_ms", 0), 1),
                "stop_reason": response_data.get("stop_reason", ""),
            },
            "conversation": {
                "messages": messages,
                "assistant_response": assistant_text,
            },
        }

    def _extract_system(self, request_data: dict) -> str | None:
        system = request_data.get("system")
        if system is None:
            return None
        if isinstance(system, str):
            return system
        if isinstance(system, list):
            return " ".join(
                block.get("text", "") for block in system if isinstance(block, dict)
            )
        return str(system)

    def _compute_context(self, tokens: dict, messages: list) -> dict:
        total_input = (
            tokens["input_tokens"]
            + tokens["cache_creation_input_tokens"]
            + tokens["cache_read_input_tokens"]
        )
        per_message = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                length = len(content)
            elif isinstance(content, list):
                length = sum(
                    len(json.dumps(block)) for block in content
                )
            else:
                length = 0
            per_message.append({"role": msg.get("role", ""), "length": length})

        return {
            "occupancy_pct": round((total_input / 200_000) * 100, 2),
            "num_turns": len(messages),
            "per_message_lengths": per_message,
        }

    def _extract_tools_from_blocks(self, blocks: list) -> list:
        tools = []
        tool_index = 0
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                tools.append({
                    "index": tool_index,
                    "name": block.get("name", ""),
                    "input": block.get("input", {}),
                    "result": None,
                })
                tool_index += 1
        return tools
