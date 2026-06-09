#!/usr/bin/env python3
"""Re-score existing benchmark sessions without re-running Claude."""

import argparse
import json
from pathlib import Path

from benchmarks.external.swebench import SWEBenchBenchmark


def rescore_session(session_dir: Path) -> None:
    """Re-score a single session directory."""

    # Extract instance info from session directory name
    # Format: session_swebench-{instance_id}_{hash}
    session_name = session_dir.name
    if not session_name.startswith("session_swebench-"):
        print(f"Skipping non-swebench session: {session_name}")
        return

    # Extract instance_id from session name
    # session_swebench-astropy__astropy-12907_3caee9e6 -> astropy__astropy-12907
    parts = session_name.replace("session_swebench-", "").rsplit("_", 1)
    instance_id = parts[0]

    print(f"\nRe-scoring: {instance_id}")

    # Find workspace directory
    workspace_dir = session_dir / "workspace" / "swebench_workspaces" / instance_id.replace("/", "_")
    if not workspace_dir.exists():
        print(f"  [ERROR] Workspace not found: {workspace_dir}")
        return

    # Load instance data from HuggingFace dataset
    try:
        from datasets import load_dataset
        dataset = load_dataset("SWE-bench/SWE-bench_Lite", split="test")
        instance_data = None
        for row in dataset:
            if row["instance_id"] == instance_id:
                instance_data = dict(row)
                break

        if not instance_data:
            print(f"  [ERROR] Instance not found in dataset: {instance_id}")
            return
    except Exception as e:
        print(f"  [ERROR] Failed to load dataset: {e}")
        return

    # Create benchmark instance
    benchmark = SWEBenchBenchmark(instance_id=instance_id, instance_data=instance_data)
    benchmark._work_dir = workspace_dir
    benchmark._workspace_base = session_dir / "workspace"

    # Re-score
    print(f"  Running tests...")
    score = benchmark.score(session_dir)

    # Save result
    result_file = session_dir / "rescore_result.json"
    result_file.write_text(json.dumps({
        "instance_id": instance_id,
        "score": score,
    }, indent=2))

    score_str = f"{score:.2f}" if score is not None else "n/a"
    print(f"  Score: {score_str}")

    # Check if test output exists
    eval_dir = workspace_dir.parent / f"eval_{instance_id}"
    test_output = eval_dir / "test_output.txt"
    if test_output.exists():
        print(f"  Test output: {test_output}")


def main():
    parser = argparse.ArgumentParser(description="Re-score benchmark sessions")
    parser.add_argument("--log-dir", default="logs", help="Log directory")
    parser.add_argument("--session", type=str, help="Specific session ID to re-score")
    parser.add_argument("--all", action="store_true", help="Re-score all swebench sessions")

    args = parser.parse_args()

    log_dir = Path(args.log_dir)
    if not log_dir.exists():
        print(f"Log directory not found: {log_dir}")
        return

    if args.session:
        # Re-score specific session
        session_dir = log_dir / f"session_{args.session}"
        if not session_dir.exists():
            session_dir = log_dir / args.session
        if not session_dir.exists():
            print(f"Session not found: {args.session}")
            return
        rescore_session(session_dir)
    elif args.all:
        # Re-score all swebench sessions
        sessions = sorted([d for d in log_dir.iterdir() if d.is_dir() and "swebench" in d.name])
        print(f"Found {len(sessions)} swebench session(s)")
        for session_dir in sessions:
            rescore_session(session_dir)
    else:
        print("Please specify --session <id> or --all")


if __name__ == "__main__":
    main()
