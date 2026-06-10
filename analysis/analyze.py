#!/usr/bin/env python3
"""
Benchmark Log Inefficiency Analysis

Extracts coding agent inefficiency patterns from Claude Code benchmark sessions.
Run one stage at a time: python3 analysis/analyze.py --stage 0
"""

import argparse
import csv
import hashlib
import json
import re
import shlex
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LOGS_DIR = Path(__file__).parent.parent / "logs"
OUTPUT_DIR = Path(__file__).parent / "output"

ZERO_WIDTH_CHARS = {"​", "‌", "‍", "﻿"}

FILE_WRITE_REDIRECTS = re.compile(
    r"""(?:^|&&|\|\||;)\s*"""
    r"""(?:cat|echo|printf)\s+.*?"""
    r"""(?:>>?)\s*"""
    r"""(?:["']?)([^\s"'|;&><]+)""",
    re.VERBOSE,
)

REDIRECT_PATTERN = re.compile(
    r"""(?<!\d)>>?\s*(?:["']?)([^\s"'|;&><]+)"""
)

TEE_PATTERN = re.compile(
    r"""tee\s+(?:-a\s+)?(?:["']?)([^\s"'|;&><]+)"""
)

SED_INPLACE_PATTERN = re.compile(
    r"""sed\s+(?:-[^i]*)?-i(?:\s*['"]?\s*[^'"]*['"]?)?\s+.*?\s+(?:["']?)([^\s"'|;&><]+)\s*$"""
)

PATCH_PATTERN = re.compile(
    r"""(?:patch|git\s+apply)"""
)

ERROR_PATTERNS = {
    "Syntax": re.compile(r"SyntaxError|IndentationError|compile.*error|build.*fail", re.IGNORECASE),
    "NotFound": re.compile(r"No such file|command not found|ModuleNotFoundError|ImportError|not found|FileNotFoundError", re.IGNORECASE),
    "TestFailed": re.compile(r"FAILED|AssertionError|assert.*fail|pytest.*fail", re.IGNORECASE),
    "Timeout": re.compile(r"timed?\s*out|timeout|time limit", re.IGNORECASE),
}

ACTION_READ_CMDS = {"cat", "head", "tail", "less", "more", "bat"}
ACTION_SEARCH_CMDS = {"grep", "find", "ls", "tree", "wc", "du", "rg", "ag", "fd"}
ACTION_TEST_CMDS = {"pytest", "python", "python3", "node", "npm", "make", "cargo"}
ACTION_VCS_CMDS = {"git-log", "git-show", "git-diff", "git-blame", "git-branch",
                   "git-tag", "git-status", "git-add", "git-commit", "git-push",
                   "git-pull", "git-fetch", "git-merge", "git-rebase", "git-cherry-pick"}
ACTION_ROLLBACK_CMDS = {"git-checkout", "git-reset", "git-stash"}


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class ToolEvent:
    session_id: str = ""
    benchmark: str = ""
    global_turn_idx: int = 0
    source_call_index: int = 0
    tool_name: str = ""
    tool_input_key: str = ""
    tool_input_hash: str = ""
    target_path: str = ""
    is_file_write: int = 0
    action_class: str = ""
    error_type: str = ""
    cmd_program: str = ""
    cmd_full_len: int = 0
    is_error: int = 0
    result_len: int = 0
    latency_ms: float = 0.0
    occupancy_pct: float = 0.0
    cache_read_input_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0


# ---------------------------------------------------------------------------
# Session Discovery
# ---------------------------------------------------------------------------

def discover_sessions(logs_dir: Path) -> list[dict]:
    sessions = []
    if not logs_dir.exists():
        return sessions
    for d in sorted(logs_dir.iterdir()):
        if not d.is_dir() or not d.name.startswith("session_"):
            continue
        name_part = d.name[len("session_"):]
        # Split off trailing _<8-char-hash>
        parts = name_part.rsplit("_", 1)
        if len(parts) == 2 and len(parts[1]) == 8:
            bench_name = parts[0]
        else:
            bench_name = name_part

        if bench_name.startswith("swebench-"):
            bench_type = "swebench"
        elif bench_name.startswith("terminalbench-"):
            bench_type = "terminalbench"
        else:
            bench_type = "open"

        sessions.append({
            "path": d,
            "session_id": name_part,
            "benchmark_name": bench_name,
            "benchmark_type": bench_type,
        })
    return sessions


def get_call_files(session_dir: Path) -> list[Path]:
    files = sorted(session_dir.glob("call_*.json"), key=lambda p: p.name)
    return files


# ---------------------------------------------------------------------------
# Call Loading
# ---------------------------------------------------------------------------

def load_call(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_title_generation_call(call_data: dict) -> bool:
    sp = call_data.get("meta", {}).get("system_prompt", "")
    return "title" in sp.lower() and "session" in sp.lower() and call_data.get("meta", {}).get("call_index", 0) <= 1


# ---------------------------------------------------------------------------
# Tool ID → Call Index Mapping
# ---------------------------------------------------------------------------

def build_tool_id_to_call_map(call_files: list[Path]) -> dict[str, int]:
    """Map tool_use_id → call_index by scanning calls in order.

    Messages are cumulative: call_N contains all messages from call_1..N.
    A tool_use_id's first appearance identifies the call that produced it.
    """
    seen_ids: set[str] = set()
    mapping: dict[str, int] = {}

    for cf in call_files:
        call_data = load_call(cf)
        call_index = call_data.get("meta", {}).get("call_index", 0)
        if is_title_generation_call(call_data):
            continue

        messages = call_data.get("conversation", {}).get("messages", [])
        for msg in messages:
            if msg.get("role") != "assistant":
                continue
            content = msg.get("content", [])
            if isinstance(content, str):
                continue
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_id = block.get("id", "")
                    if tool_id and tool_id not in seen_ids:
                        seen_ids.add(tool_id)
                        mapping[tool_id] = call_index

    return mapping


def build_call_metadata(call_files: list[Path]) -> dict[int, dict]:
    """Map call_index → {latency_ms, occupancy_pct, tokens...}."""
    metadata = {}
    for cf in call_files:
        call_data = load_call(cf)
        call_index = call_data.get("meta", {}).get("call_index", 0)
        if is_title_generation_call(call_data):
            continue
        metadata[call_index] = {
            "latency_ms": call_data.get("performance", {}).get("latency_ms", 0),
            "occupancy_pct": call_data.get("context", {}).get("occupancy_pct", 0),
            "input_tokens": call_data.get("tokens", {}).get("input_tokens", 0),
            "output_tokens": call_data.get("tokens", {}).get("output_tokens", 0),
            "cache_read_input_tokens": call_data.get("tokens", {}).get("cache_read_input_tokens", 0),
        }
    return metadata


# ---------------------------------------------------------------------------
# Bash Command Parser
# ---------------------------------------------------------------------------

def parse_cmd_program(command: str) -> str:
    """Extract the primary program from a Bash command string."""
    if not command or not command.strip():
        return ""

    cmd = command.strip()

    # Remove leading environment variable assignments
    while re.match(r'^[A-Z_][A-Z0-9_]*=\S*\s+', cmd):
        cmd = re.sub(r'^[A-Z_][A-Z0-9_]*=\S*\s+', '', cmd)

    # Handle pipes: take first command segment
    # But ignore trailing pipes to head/tail (display only)
    pipe_segments = re.split(r'\s*\|\s*', cmd)
    cmd = pipe_segments[0].strip()

    # Handle command chaining (&&, ||, ;) — take first
    cmd = re.split(r'\s*(?:&&|\|\||;)\s*', cmd)[0].strip()

    # Handle subshell/group
    cmd = cmd.lstrip("(").lstrip("{").strip()

    # Remove leading redirections like 2>&1
    cmd = re.sub(r'^\d*>&\d+\s*', '', cmd).strip()

    # Try shlex
    try:
        tokens = shlex.split(cmd)
    except ValueError:
        # Fallback: split on whitespace
        tokens = cmd.split()

    if not tokens:
        return ""

    program = tokens[0]

    # Strip path prefix
    if "/" in program:
        program = program.rsplit("/", 1)[-1]

    # Handle git subcommands
    if program == "git" and len(tokens) > 1:
        sub = tokens[1]
        if not sub.startswith("-"):
            return f"git-{sub}"
        return "git"

    # Handle python -m <module>
    if program in ("python", "python3") and len(tokens) > 1:
        if tokens[1] == "-m" and len(tokens) > 2:
            module = tokens[2]
            return module  # e.g., "pytest", "pip"
        if tokens[1] == "-c":
            return "python-c"

    # Handle cd (often in compound commands that we already split)
    return program


def extract_bash_target_path(command: str) -> tuple[str, bool]:
    """Extract target file path from Bash file-write commands.
    Returns (target_path, is_file_write).
    """
    if not command:
        return "", False

    # patch / git apply → file write but unknown target
    if PATCH_PATTERN.search(command):
        return "", True

    # sed -i
    sed_match = re.search(r"sed\s+.*-i\b", command)
    if sed_match:
        # Extract last non-option argument as file path
        # Simplified: look for file path after the sed expression
        parts = command.split()
        # Find file args (skip flags and expressions)
        candidates = []
        skip_next = False
        for i, p in enumerate(parts):
            if skip_next:
                skip_next = False
                continue
            if p == "sed" or p.startswith("-"):
                if p in ("-e", "-f") or (p.startswith("-") and "i" not in p):
                    skip_next = True
                continue
            # Skip quoted sed expressions
            if p.startswith(("'", '"', "s/", "s|")):
                continue
            candidates.append(p)
        if candidates:
            path = candidates[-1].strip("'\"")
            return path, True
        return "", True

    # tee
    tee_match = TEE_PATTERN.search(command)
    if tee_match:
        return tee_match.group(1).strip("'\""), True

    # Redirect: > or >> (but NOT 2> or 1> or &>)
    # Find redirects that are actual file writes
    redirect_match = re.search(r'(?<!\d)(?<!&)>>?\s*(?:["\'`]?)([^\s"\'`|;&><\)]+)', command)
    if redirect_match:
        path = redirect_match.group(1).strip("'\"`")
        # Filter out /dev/null and fd targets
        if path.startswith("/dev/") or path.isdigit():
            return "", False
        return path, True

    return "", False


def classify_action(tool_name: str, tool_input: dict, cmd_program: str, is_file_write: bool) -> str:
    """Classify a tool call into an action category."""
    if tool_name == "Read":
        return "read"
    if tool_name == "Write":
        return "file_write"
    if tool_name == "Edit":
        return "file_modify"

    if tool_name == "Bash":
        if is_file_write:
            return "file_modify"
        if cmd_program in ACTION_ROLLBACK_CMDS:
            return "rollback"
        if cmd_program in ACTION_VCS_CMDS:
            return "vcs"
        if cmd_program in ACTION_SEARCH_CMDS:
            return "search"
        if cmd_program in ACTION_READ_CMDS:
            return "read"
        if cmd_program in ACTION_TEST_CMDS:
            return "exec_test"
        # git without recognized subcommand
        if cmd_program.startswith("git-"):
            return "vcs"

    return "other"


def classify_error(content: str) -> str:
    """Classify error type from tool_result content."""
    if not content:
        return "Other"
    for etype, pattern in ERROR_PATTERNS.items():
        if pattern.search(content[:2000]):
            return etype
    return "Other"


def compute_tool_input_key(tool_name: str, tool_input: dict) -> str:
    """Extract a human-readable key from tool input."""
    if tool_name == "Read":
        return tool_input.get("file_path", "")
    if tool_name in ("Edit", "Write"):
        return tool_input.get("file_path", "")
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        return cmd[:80]
    # Other tools: first value
    for k, v in tool_input.items():
        return str(v)[:80]
    return ""


def compute_tool_input_hash(tool_name: str, tool_input: dict) -> str:
    """Compute a normalized hash of tool input for dedup detection."""
    # Normalize: compress whitespace but keep paths
    normalized = json.dumps({"name": tool_name, "input": tool_input}, sort_keys=True)
    normalized = re.sub(r'\s+', ' ', normalized)
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Session Parser
# ---------------------------------------------------------------------------

def parse_session_events(session_info: dict) -> list[ToolEvent]:
    """Parse all tool events from a session.

    Strategy: scan call files in order. Each call's messages are cumulative,
    so we track which tool_use ids we've already processed. For each new
    tool_use we encounter, we record it with that call's metadata.
    tool_results are collected across all calls (last occurrence wins).
    """
    session_dir = session_info["path"]
    call_files = get_call_files(session_dir)

    if not call_files:
        return []

    # Pass 1: Build tool_id → call_index mapping and call metadata
    tool_id_to_call = build_tool_id_to_call_map(call_files)
    call_metadata = build_call_metadata(call_files)

    # Pass 2: Collect all tool_results from all calls (last call has the most complete set)
    # We use the last call's messages since it's cumulative and has all results
    # But also scan earlier calls in case of context truncation
    tool_results: dict[str, dict] = {}
    for cf in call_files:
        call_data = load_call(cf)
        if is_title_generation_call(call_data):
            continue
        messages = call_data.get("conversation", {}).get("messages", [])
        for msg in messages:
            if msg.get("role") != "user":
                continue
            content = msg.get("content", [])
            if isinstance(content, str):
                continue
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    tid = block.get("tool_use_id", "")
                    if tid:
                        result_content = block.get("content", "")
                        if isinstance(result_content, list):
                            result_content = json.dumps(result_content)
                        tool_results[tid] = {
                            "content": str(result_content) if result_content else "",
                            "is_error": bool(block.get("is_error", False)),
                        }

    # Pass 3: Collect all tool_use blocks in order (deduplicated by id)
    # Using the last call's messages for ordering (it's the most complete),
    # but we already have call_index from the mapping built in pass 1.
    last_call = load_call(call_files[-1])
    messages = last_call.get("conversation", {}).get("messages", [])

    # If last call is title gen (unlikely), fall back to second-to-last
    if is_title_generation_call(last_call) and len(call_files) > 1:
        last_call = load_call(call_files[-2])
        messages = last_call.get("conversation", {}).get("messages", [])

    # Extract tool_use events in conversation order
    events = []
    seen_tool_ids: set[str] = set()
    global_turn_idx = 0

    for msg in messages:
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content", [])
        if isinstance(content, str):
            continue

        for block in content:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue

            tool_id = block.get("id", "")
            # Deduplicate (messages are cumulative, same tool_use appears in later calls)
            if tool_id in seen_tool_ids:
                continue
            seen_tool_ids.add(tool_id)

            tool_name = block.get("name", "")
            tool_input = block.get("input", {})

            # Get call metadata via the mapping
            call_index = tool_id_to_call.get(tool_id, 0)
            meta = call_metadata.get(call_index, {})

            # Bash-specific parsing
            cmd_program = ""
            cmd_full_len = 0
            target_path = ""
            is_file_write = False

            if tool_name == "Bash":
                command = tool_input.get("command", "")
                cmd_program = parse_cmd_program(command)
                cmd_full_len = len(command)
                target_path, is_file_write = extract_bash_target_path(command)
            elif tool_name in ("Edit", "Write"):
                target_path = tool_input.get("file_path", "")
                is_file_write = True
            elif tool_name == "Read":
                target_path = tool_input.get("file_path", "")

            # Get result info
            result_info = tool_results.get(tool_id, {})
            is_error = result_info.get("is_error", False)
            result_content = result_info.get("content", "")
            result_len = len(result_content) if result_content else 0

            # Classify
            action_class = classify_action(tool_name, tool_input, cmd_program, is_file_write)
            error_type = classify_error(result_content) if is_error else ""

            event = ToolEvent(
                session_id=session_info["session_id"],
                benchmark=session_info["benchmark_type"],
                global_turn_idx=global_turn_idx,
                source_call_index=call_index,
                tool_name=tool_name,
                tool_input_key=compute_tool_input_key(tool_name, tool_input),
                tool_input_hash=compute_tool_input_hash(tool_name, tool_input),
                target_path=target_path,
                is_file_write=1 if is_file_write else 0,
                action_class=action_class,
                error_type=error_type,
                cmd_program=cmd_program,
                cmd_full_len=cmd_full_len,
                is_error=1 if is_error else 0,
                result_len=result_len,
                latency_ms=meta.get("latency_ms", 0),
                occupancy_pct=meta.get("occupancy_pct", 0),
                cache_read_input_tokens=meta.get("cache_read_input_tokens", 0),
                input_tokens=meta.get("input_tokens", 0),
                output_tokens=meta.get("output_tokens", 0),
            )
            events.append(event)
            global_turn_idx += 1

    return events


# ---------------------------------------------------------------------------
# Stage 0: Validation
# ---------------------------------------------------------------------------

def run_stage_0(logs_dir: Path):
    """Per-benchmark single-session validation."""
    sessions = discover_sessions(logs_dir)
    if not sessions:
        print("No sessions found.")
        return

    # Group by benchmark type
    by_type = defaultdict(list)
    for s in sessions:
        by_type[s["benchmark_type"]].append(s)

    print(f"Found {len(sessions)} sessions across {len(by_type)} benchmark types:")
    for btype, sess_list in sorted(by_type.items()):
        print(f"  {btype}: {len(sess_list)} sessions")
    print()

    validation = {}

    for btype, sess_list in sorted(by_type.items()):
        # Pick the session with the most call files
        best_session = max(sess_list, key=lambda s: len(get_call_files(s["path"])))
        print(f"{'='*70}")
        print(f"Benchmark: {btype} | Session: {best_session['session_id']}")
        print(f"{'='*70}")

        call_files = get_call_files(best_session["path"])
        print(f"  Call files: {len(call_files)}")

        # Parse events
        events = parse_session_events(best_session)
        print(f"  Total tool events: {len(events)}")

        if not events:
            print("  (no events parsed, skipping)")
            validation[btype] = {"status": "no_events"}
            continue

        # (a) ID matching sample
        print(f"\n  (a) ID matching samples:")
        shown = 0
        for e in events[:10]:
            if shown >= 3:
                break
            print(f"      turn={e.global_turn_idx} tool={e.tool_name} "
                  f"call_idx={e.source_call_index} "
                  f"error={e.is_error} result_len={e.result_len}")
            shown += 1

        # (b) cmd_program parsing samples
        bash_events = [e for e in events if e.tool_name == "Bash"]
        print(f"\n  (b) cmd_program parsing ({len(bash_events)} Bash calls):")
        for e in bash_events[:5]:
            print(f"      cmd_program={e.cmd_program!r:20s} | input_key={e.tool_input_key!r}")

        # (c) Tool distribution
        tool_dist = Counter(e.tool_name for e in events)
        print(f"\n  (c) Tool distribution:")
        for name, count in tool_dist.most_common():
            print(f"      {name}: {count}")

        # (d) File modification methods
        file_mods = [e for e in events if e.is_file_write]
        mod_methods = Counter(e.tool_name for e in file_mods)
        print(f"\n  (d) File modification methods ({len(file_mods)} total):")
        for name, count in mod_methods.most_common():
            print(f"      {name}: {count}")

        # (e) Error type samples
        errors = [e for e in events if e.is_error]
        error_types = Counter(e.error_type for e in errors)
        print(f"\n  (e) Error types ({len(errors)} errors):")
        for etype, count in error_types.most_common():
            print(f"      {etype}: {count}")
        if errors:
            sample_err = errors[0]
            print(f"      Sample: tool={sample_err.tool_name} "
                  f"cmd={sample_err.cmd_program!r} "
                  f"error_type={sample_err.error_type}")

        # Action class distribution
        action_dist = Counter(e.action_class for e in events)
        print(f"\n  Action class distribution:")
        for ac, count in action_dist.most_common():
            print(f"      {ac}: {count}")

        validation[btype] = {
            "session_id": best_session["session_id"],
            "num_calls": len(call_files),
            "num_events": len(events),
            "tool_distribution": dict(tool_dist),
            "action_distribution": dict(action_dist),
            "error_types": dict(error_types),
            "file_mod_methods": dict(mod_methods),
            "bash_count": len(bash_events),
        }
        print()

    # Cross-benchmark comparison
    print(f"\n{'='*70}")
    print("Cross-benchmark comparison")
    print(f"{'='*70}")
    print(f"\n{'Benchmark':<15} {'Events':<8} {'Bash%':<8} {'Edit%':<8} {'Read%':<8} {'Errors':<8} {'FileMods':<8}")
    print("-" * 70)
    for btype, v in sorted(validation.items()):
        if v.get("status") == "no_events":
            print(f"{btype:<15} (no events)")
            continue
        n = v["num_events"]
        bash_pct = v["tool_distribution"].get("Bash", 0) / n * 100 if n else 0
        edit_pct = v["tool_distribution"].get("Edit", 0) / n * 100 if n else 0
        read_pct = v["tool_distribution"].get("Read", 0) / n * 100 if n else 0
        errors = sum(v["error_types"].values())
        file_mods = sum(v["file_mod_methods"].values())
        print(f"{btype:<15} {n:<8} {bash_pct:<8.1f} {edit_pct:<8.1f} {read_pct:<8.1f} {errors:<8} {file_mods:<8}")

    # Save validation output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "stage0_validation.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(validation, f, indent=2, default=str)
    print(f"\nValidation saved to: {output_path}")


# ---------------------------------------------------------------------------
# Stage 1: Generate events.jsonl
# ---------------------------------------------------------------------------

def run_stage_1(logs_dir: Path):
    """Generate events.jsonl with one row per tool_use."""
    sessions = discover_sessions(logs_dir)
    if not sessions:
        print("No sessions found.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "events.jsonl"
    total_events = 0
    session_count = 0

    with open(output_path, "w", encoding="utf-8") as f:
        for session_info in sessions:
            events = parse_session_events(session_info)
            for event in events:
                f.write(json.dumps(asdict(event), default=str) + "\n")
            total_events += len(events)
            session_count += 1
            if events:
                print(f"  {session_info['session_id']}: {len(events)} events")

    print(f"\nTotal: {total_events} events from {session_count} sessions")
    print(f"Output: {output_path}")


# ---------------------------------------------------------------------------
# Stage 2: Generate session_metrics.csv
# ---------------------------------------------------------------------------

def compute_session_metrics(session_id: str, events: list[ToolEvent], call_files: list[Path]) -> dict:
    """Compute aggregate metrics for a session."""
    if not events:
        return {}

    benchmark = events[0].benchmark

    # Basic counts
    total_tool_uses = len(events)
    error_count = sum(1 for e in events if e.is_error)
    error_rate = error_count / total_tool_uses if total_tool_uses else 0

    # Error breakdown
    error_breakdown = Counter(e.error_type for e in events if e.is_error)

    # Token/cost/latency from call files
    # NOTE: tokens are summed per-call (= actual billed tokens).
    # Each call's input_tokens reflects what was charged for that request,
    # NOT cumulative unique content (cache_read covers re-sent context).
    # This matches API billing semantics: total_cost = sum of per-call costs.
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost = 0.0
    total_latency_ms = 0.0
    total_calls = 0

    for cf in call_files:
        call_data = load_call(cf)
        if is_title_generation_call(call_data):
            continue
        total_calls += 1
        tokens = call_data.get("tokens", {})
        total_input_tokens += tokens.get("input_tokens", 0) + tokens.get("cache_read_input_tokens", 0)
        total_output_tokens += tokens.get("output_tokens", 0)
        total_cost += call_data.get("cost", {}).get("total_cost", 0)
        total_latency_ms += call_data.get("performance", {}).get("latency_ms", 0)

    # Redundant tool calls (same hash 2+ times)
    hash_counts = Counter(e.tool_input_hash for e in events)
    redundant_tool_calls = sum(c - 1 for c in hash_counts.values() if c > 1)

    # Max consecutive errors
    max_consec_errors = 0
    current_streak = 0
    for e in events:
        if e.is_error:
            current_streak += 1
            max_consec_errors = max(max_consec_errors, current_streak)
        else:
            current_streak = 0

    # Retry after error: tool call immediately after an error with same tool_name
    retry_after_error = 0
    for i in range(1, len(events)):
        if events[i - 1].is_error and events[i].tool_name == events[i - 1].tool_name:
            retry_after_error += 1

    # File reads
    read_paths = [e.target_path for e in events if e.tool_name == "Read" and e.target_path]
    distinct_files_read = len(set(read_paths))
    repeated_file_reads = len(read_paths) - distinct_files_read

    # Read but unused files
    has_patch = any(e.action_class in ("file_modify",) and e.cmd_program in ("patch", "git-apply") for e in events)
    if has_patch:
        read_but_unused = "N/A"
    else:
        modified_paths = set(e.target_path for e in events if e.is_file_write and e.target_path)
        read_only_paths = set(read_paths) - modified_paths
        read_but_unused = str(len(read_only_paths))

    # Repeated file modifications
    mod_paths = [e.target_path for e in events if e.is_file_write and e.target_path]
    mod_path_counts = Counter(mod_paths)
    repeated_file_modifications = sum(c - 1 for c in mod_path_counts.values() if c > 1)

    # File writes via Bash
    file_writes_via_bash = sum(1 for e in events if e.is_file_write and e.tool_name == "Bash")

    # Rollback and stash
    rollback_count = sum(1 for e in events if e.action_class == "rollback" and e.cmd_program != "git-stash")
    stash_count = sum(1 for e in events if e.cmd_program == "git-stash")

    # Cache hit ratio (per-call average)
    cache_ratios = []
    for cf in call_files:
        call_data = load_call(cf)
        if is_title_generation_call(call_data):
            continue
        tokens = call_data.get("tokens", {})
        cache_read = tokens.get("cache_read_input_tokens", 0)
        input_t = tokens.get("input_tokens", 0)
        denom = input_t + cache_read
        if denom > 0:
            cache_ratios.append(cache_read / denom)
    avg_cache_hit_ratio = sum(cache_ratios) / len(cache_ratios) if cache_ratios else 0

    # Occupancy
    occupancies = [e.occupancy_pct for e in events if e.occupancy_pct > 0]
    max_occupancy_pct = max(occupancies) if occupancies else 0
    min_occupancy = min(occupancies) if occupancies else 0
    occupancy_growth = max_occupancy_pct - min_occupancy

    # Max tokens hit
    max_tokens_hit_count = 0
    for cf in call_files:
        call_data = load_call(cf)
        if call_data.get("performance", {}).get("stop_reason") == "max_tokens":
            max_tokens_hit_count += 1

    # Final stop reason
    last_call = load_call(call_files[-1])
    final_stop_reason = last_call.get("performance", {}).get("stop_reason", "")

    return {
        "session_id": session_id,
        "benchmark": benchmark,
        "total_calls": total_calls,
        "total_tool_uses": total_tool_uses,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_cost": round(total_cost, 6),
        "total_latency_sec": round(total_latency_ms / 1000, 2),
        "redundant_tool_calls": redundant_tool_calls,
        "error_count": error_count,
        "error_rate": round(error_rate, 4),
        "error_breakdown_Syntax": error_breakdown.get("Syntax", 0),
        "error_breakdown_NotFound": error_breakdown.get("NotFound", 0),
        "error_breakdown_TestFailed": error_breakdown.get("TestFailed", 0),
        "error_breakdown_Timeout": error_breakdown.get("Timeout", 0),
        "error_breakdown_Other": error_breakdown.get("Other", 0),
        "max_consecutive_errors": max_consec_errors,
        "retry_after_error": retry_after_error,
        "distinct_files_read": distinct_files_read,
        "repeated_file_reads": repeated_file_reads,
        "read_but_unused_files": read_but_unused,
        "repeated_file_modifications": repeated_file_modifications,
        "file_writes_via_bash": file_writes_via_bash,
        "rollback_count": rollback_count,
        "stash_count": stash_count,
        "average_cache_hit_ratio": round(avg_cache_hit_ratio, 4),
        "max_occupancy_pct": round(max_occupancy_pct, 2),
        "occupancy_growth": round(occupancy_growth, 2),
        "max_tokens_hit_count": max_tokens_hit_count,
        "final_stop_reason": final_stop_reason,
    }


def run_stage_2(logs_dir: Path):
    """Generate session_metrics.csv."""
    # Read events from stage 1
    events_path = OUTPUT_DIR / "events.jsonl"
    if not events_path.exists():
        print("Error: events.jsonl not found. Run --stage 1 first.")
        return

    # Load all events
    events_by_session = defaultdict(list)
    with open(events_path, "r") as f:
        for line in f:
            event_dict = json.loads(line)
            event = ToolEvent(**event_dict)
            events_by_session[event.session_id].append(event)

    sessions = discover_sessions(logs_dir)
    session_map = {s["session_id"]: s for s in sessions}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "session_metrics.csv"

    all_metrics = []
    for session_id, events in sorted(events_by_session.items()):
        session_info = session_map.get(session_id)
        if not session_info:
            continue
        call_files = get_call_files(session_info["path"])
        metrics = compute_session_metrics(session_id, events, call_files)
        if metrics:
            all_metrics.append(metrics)

    if not all_metrics:
        print("No metrics computed.")
        return

    # Write CSV
    fieldnames = list(all_metrics[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_metrics:
            writer.writerow(row)

    print(f"Session metrics saved: {output_path}")
    print(f"Total sessions: {len(all_metrics)}")

    # Print summary
    print(f"\n{'Session':<50} {'Cost':<8} {'Errors':<8} {'Redundant':<10} {'Rollback':<10}")
    print("-" * 90)
    for m in sorted(all_metrics, key=lambda x: x["total_cost"], reverse=True)[:10]:
        print(f"{m['session_id'][:48]:<50} ${m['total_cost']:<7.4f} {m['error_count']:<8} "
              f"{m['redundant_tool_calls']:<10} {m['rollback_count']:<10}")


# ---------------------------------------------------------------------------
# Stage 3 & 4: Analysis (markdown generation)
# ---------------------------------------------------------------------------

def run_stage_3(logs_dir: Path):
    """Generate per_session_analysis.md."""
    events_path = OUTPUT_DIR / "events.jsonl"
    metrics_path = OUTPUT_DIR / "session_metrics.csv"

    if not events_path.exists() or not metrics_path.exists():
        print("Error: Run stages 1 and 2 first.")
        return

    # Load metrics
    with open(metrics_path, "r") as f:
        reader = csv.DictReader(f)
        metrics = list(reader)

    # Load events
    events_by_session = defaultdict(list)
    with open(events_path, "r") as f:
        for line in f:
            event_dict = json.loads(line)
            events_by_session[event_dict["session_id"]].append(event_dict)

    output_path = OUTPUT_DIR / "per_session_analysis.md"
    lines = ["# Per-Session Analysis\n"]

    # Sort by inefficiency indicators
    def inefficiency_score(m):
        return (
            int(m.get("error_count", 0)) * 2
            + int(m.get("redundant_tool_calls", 0))
            + int(m.get("repeated_file_modifications", 0)) * 3
            + int(m.get("rollback_count", 0)) * 5
        )

    metrics_sorted = sorted(metrics, key=inefficiency_score, reverse=True)

    for m in metrics_sorted[:15]:  # Top 15 most inefficient
        sid = m["session_id"]
        lines.append(f"\n## {sid}\n")
        lines.append(f"- Benchmark: {m['benchmark']}")
        lines.append(f"- Total calls: {m['total_calls']}, Tool uses: {m['total_tool_uses']}")
        lines.append(f"- Cost: ${m['total_cost']}, Latency: {m['total_latency_sec']}s")
        lines.append(f"- Errors: {m['error_count']} (rate: {m['error_rate']})")
        lines.append(f"  - Syntax: {m['error_breakdown_Syntax']}, NotFound: {m['error_breakdown_NotFound']}, "
                     f"TestFailed: {m['error_breakdown_TestFailed']}, Timeout: {m['error_breakdown_Timeout']}")
        lines.append(f"- Redundant calls: {m['redundant_tool_calls']}")
        lines.append(f"- Repeated file modifications: {m['repeated_file_modifications']}")
        lines.append(f"- Rollbacks: {m['rollback_count']}, Stashes: {m['stash_count']}")
        lines.append(f"- Max consecutive errors: {m['max_consecutive_errors']}")
        lines.append(f"- Cache hit ratio: {m['average_cache_hit_ratio']}")
        lines.append(f"- Occupancy: max={m['max_occupancy_pct']}%, growth={m['occupancy_growth']}%")
        lines.append(f"- Read but unused files: {m['read_but_unused_files']}")

        # Trace: show error sequences
        session_events = events_by_session.get(sid, [])
        error_sequences = []
        current_seq = []
        for e in session_events:
            if e["is_error"]:
                current_seq.append(e)
            else:
                if len(current_seq) >= 2:
                    error_sequences.append(current_seq)
                current_seq = []
        if len(current_seq) >= 2:
            error_sequences.append(current_seq)

        if error_sequences:
            lines.append(f"\n### Error sequences ({len(error_sequences)} sequences of 2+ consecutive errors)")
            for i, seq in enumerate(error_sequences[:3]):
                lines.append(f"\n  Sequence {i+1} (turns {seq[0]['global_turn_idx']}-{seq[-1]['global_turn_idx']}):")
                for e in seq[:5]:
                    lines.append(f"    - [{e['tool_name']}] {e['cmd_program'] or e['tool_input_key'][:40]} "
                                 f"→ {e['error_type']}")

        # Repeated modifications
        mod_events = [e for e in session_events if e["is_file_write"] and e["target_path"]]
        path_counts = Counter(e["target_path"] for e in mod_events)
        repeated = [(p, c) for p, c in path_counts.items() if c > 1]
        if repeated:
            lines.append(f"\n### Repeated file modifications")
            for path, count in sorted(repeated, key=lambda x: -x[1])[:5]:
                lines.append(f"  - {path}: {count} times")

        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Per-session analysis saved: {output_path}")


def run_stage_4(logs_dir: Path):
    """Generate overall_analysis.md."""
    events_path = OUTPUT_DIR / "events.jsonl"
    metrics_path = OUTPUT_DIR / "session_metrics.csv"

    if not events_path.exists() or not metrics_path.exists():
        print("Error: Run stages 1 and 2 first.")
        return

    # Load metrics
    with open(metrics_path, "r") as f:
        reader = csv.DictReader(f)
        metrics = list(reader)

    # Load all events
    all_events = []
    with open(events_path, "r") as f:
        for line in f:
            all_events.append(json.loads(line))

    output_path = OUTPUT_DIR / "overall_analysis.md"
    lines = ["# Overall Analysis\n"]

    # --- (a) Cross-session analysis ---
    lines.append("\n## (a) Cross-session & Cross-benchmark Analysis\n")

    # Per-benchmark comparison
    by_bench = defaultdict(list)
    for m in metrics:
        by_bench[m["benchmark"]].append(m)

    lines.append("### Benchmark Comparison\n")
    lines.append(f"| Benchmark | Sessions | Avg Cost | Avg Errors | Avg Redundant | Avg Repeated Mods | Avg Rollback | Avg Cache Hit |")
    lines.append(f"|-----------|----------|----------|------------|---------------|-------------------|--------------|---------------|")
    for bench, ms in sorted(by_bench.items()):
        n = len(ms)
        avg_cost = sum(float(m["total_cost"]) for m in ms) / n
        avg_errors = sum(int(m["error_count"]) for m in ms) / n
        avg_redundant = sum(int(m["redundant_tool_calls"]) for m in ms) / n
        avg_repeated = sum(int(m["repeated_file_modifications"]) for m in ms) / n
        avg_rollback = sum(int(m["rollback_count"]) for m in ms) / n
        avg_cache = sum(float(m["average_cache_hit_ratio"]) for m in ms) / n
        lines.append(f"| {bench} | {n} | ${avg_cost:.4f} | {avg_errors:.1f} | {avg_redundant:.1f} | {avg_repeated:.1f} | {avg_rollback:.1f} | {avg_cache:.3f} |")

    # Error type distribution by benchmark
    lines.append("\n### Error Type Distribution by Benchmark\n")
    bench_events = defaultdict(list)
    for e in all_events:
        bench_events[e["benchmark"]].append(e)

    lines.append(f"| Benchmark | Total Errors | Syntax | NotFound | TestFailed | Timeout | Other |")
    lines.append(f"|-----------|-------------|--------|----------|------------|---------|-------|")
    for bench, evts in sorted(bench_events.items()):
        errors = [e for e in evts if e["is_error"]]
        etypes = Counter(e["error_type"] for e in errors)
        lines.append(f"| {bench} | {len(errors)} | {etypes.get('Syntax',0)} | {etypes.get('NotFound',0)} | "
                     f"{etypes.get('TestFailed',0)} | {etypes.get('Timeout',0)} | {etypes.get('Other',0)} |")

    # Correlations (simple text-based)
    lines.append("\n### Metric Relationships\n")
    lines.append("(Note: with small n, these are observations, not statistically robust correlations)\n")

    for m in metrics:
        m["_error_rate_f"] = float(m["error_rate"])
        m["_cost_f"] = float(m["total_cost"])
        m["_cache_f"] = float(m["average_cache_hit_ratio"])
        m["_occupancy_f"] = float(m["max_occupancy_pct"])
        m["_repeated_f"] = int(m["repeated_file_modifications"])
        m["_rollback_f"] = int(m["rollback_count"])
        m["_latency_f"] = float(m["total_latency_sec"])

    # High error vs repeated mods
    high_error = [m for m in metrics if m["_error_rate_f"] > 0.2]
    if high_error:
        avg_repeated_high_err = sum(m["_repeated_f"] for m in high_error) / len(high_error)
        low_error = [m for m in metrics if m["_error_rate_f"] <= 0.2]
        avg_repeated_low_err = sum(m["_repeated_f"] for m in low_error) / len(low_error) if low_error else 0
        lines.append(f"- Sessions with error_rate>0.2: avg repeated_file_modifications={avg_repeated_high_err:.1f} "
                     f"(vs {avg_repeated_low_err:.1f} for error_rate<=0.2)")
        lines.append(f"  (n={len(high_error)} high-error sessions, n={len(low_error)} low-error sessions)")

    # Cache vs cost
    high_cache = [m for m in metrics if m["_cache_f"] > 0.5]
    low_cache = [m for m in metrics if m["_cache_f"] <= 0.5]
    if high_cache and low_cache:
        avg_cost_high_cache = sum(m["_cost_f"] for m in high_cache) / len(high_cache)
        avg_cost_low_cache = sum(m["_cost_f"] for m in low_cache) / len(low_cache)
        lines.append(f"- High cache hit (>0.5): avg cost=${avg_cost_high_cache:.4f} "
                     f"(vs ${avg_cost_low_cache:.4f} for low cache)")

    # Time vs tokens
    lines.append(f"\n### Time vs Tokens")
    lines.append(f"(latency_ms = model inference + tool execution, mixed; cannot separate)\n")
    for m in sorted(metrics, key=lambda x: x["_latency_f"], reverse=True)[:5]:
        lines.append(f"- {m['session_id'][:40]}: {m['_latency_f']:.1f}s, "
                     f"${m['_cost_f']:.4f}, {m['total_tool_uses']} tools")

    # --- (b) cmd_program analysis ---
    lines.append("\n\n## (b) cmd_program Analysis (Bash only)\n")

    bash_events = [e for e in all_events if e["tool_name"] == "Bash" and e["cmd_program"]]
    cmd_stats = defaultdict(lambda: {"count": 0, "errors": 0, "result_lens": [], "latencies": []})

    for e in bash_events:
        prog = e["cmd_program"]
        cmd_stats[prog]["count"] += 1
        if e["is_error"]:
            cmd_stats[prog]["errors"] += 1
        cmd_stats[prog]["result_lens"].append(e["result_len"])
        cmd_stats[prog]["latencies"].append(e["latency_ms"])

    # By frequency
    lines.append("### By frequency\n")
    lines.append(f"| Command | Count | Error Rate | Avg Result Len | Avg Latency(ms) |")
    lines.append(f"|---------|-------|------------|----------------|-----------------|")
    for prog, stats in sorted(cmd_stats.items(), key=lambda x: -x[1]["count"])[:20]:
        n = stats["count"]
        err_rate = stats["errors"] / n if n else 0
        avg_rlen = sum(stats["result_lens"]) / n if n else 0
        avg_lat = sum(stats["latencies"]) / n if n else 0
        lines.append(f"| {prog} | {n} | {err_rate:.2f} | {avg_rlen:.0f} | {avg_lat:.0f} |")

    # By error rate (min 3 calls)
    lines.append("\n### By error rate (min 3 calls)\n")
    lines.append(f"| Command | Count | Errors | Error Rate |")
    lines.append(f"|---------|-------|--------|------------|")
    for prog, stats in sorted(cmd_stats.items(), key=lambda x: -(x[1]["errors"]/x[1]["count"] if x[1]["count"]>=3 else 0)):
        n = stats["count"]
        if n < 3:
            continue
        err_rate = stats["errors"] / n
        if err_rate == 0:
            continue
        lines.append(f"| {prog} | {n} | {stats['errors']} | {err_rate:.2f} |")

    # Git subcommands
    git_events = [e for e in bash_events if e["cmd_program"].startswith("git-")]
    if git_events:
        lines.append("\n### Git subcommands\n")
        git_dist = Counter(e["cmd_program"] for e in git_events)
        lines.append(f"| Subcommand | Count |")
        lines.append(f"|------------|-------|")
        for cmd, cnt in git_dist.most_common():
            lines.append(f"| {cmd} | {cnt} |")

    # --- (c) Per-benchmark tool profiles ---
    lines.append("\n\n## (c) Per-benchmark Tool Profiles\n")

    for bench, evts in sorted(bench_events.items()):
        lines.append(f"\n### {bench} ({len(evts)} tool calls)\n")

        tool_dist = Counter(e["tool_name"] for e in evts)
        action_dist = Counter(e["action_class"] for e in evts)
        cmd_dist = Counter(e["cmd_program"] for e in evts if e["cmd_program"])

        lines.append("**Tool distribution:**")
        for name, count in tool_dist.most_common():
            pct = count / len(evts) * 100
            lines.append(f"  - {name}: {count} ({pct:.1f}%)")

        lines.append("\n**Action class distribution:**")
        for ac, count in action_dist.most_common():
            pct = count / len(evts) * 100
            lines.append(f"  - {ac}: {count} ({pct:.1f}%)")

        lines.append("\n**Top commands:**")
        for cmd, count in cmd_dist.most_common(10):
            lines.append(f"  - {cmd}: {count}")

    # Limitations
    lines.append("\n\n## Limitations & Caveats\n")
    lines.append("- result_len is character length, not tokens. Token proxy only.")
    lines.append("- read_but_unused_files measures 'not modified', not 'not referenced in reasoning'.")
    lines.append("- error_type is keyword heuristic, not 100% accurate.")
    lines.append("- TestFailed may be normal debugging, not inefficiency.")
    lines.append("- latency_ms mixes model inference wait + tool execution time; cannot separate.")
    lines.append("- cache_hit_ratio: calls with input_tokens=0 and high cache_read are normal (multi-turn cache).")
    lines.append("- Small n per benchmark type — observations are tentative, not generalizable.")

    # N/A tracking
    na_count = sum(1 for m in metrics if m.get("read_but_unused_files") == "N/A")
    lines.append(f"- Sessions with read_but_unused_files=N/A (due to patch/git apply): {na_count}/{len(metrics)}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Overall analysis saved: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Benchmark Log Inefficiency Analysis")
    parser.add_argument("--stage", type=int, required=True, choices=[0, 1, 2, 3, 4],
                        help="Stage to run (0-4)")
    parser.add_argument("--logs-dir", type=str, default=None,
                        help="Path to logs directory (default: ../logs)")
    args = parser.parse_args()

    logs_dir = Path(args.logs_dir) if args.logs_dir else LOGS_DIR

    if not logs_dir.exists():
        print(f"Error: logs directory not found: {logs_dir}")
        sys.exit(1)

    if args.stage == 0:
        run_stage_0(logs_dir)
    elif args.stage == 1:
        run_stage_1(logs_dir)
    elif args.stage == 2:
        run_stage_2(logs_dir)
    elif args.stage == 3:
        run_stage_3(logs_dir)
    elif args.stage == 4:
        run_stage_4(logs_dir)


if __name__ == "__main__":
    main()
