import argparse
import asyncio
from pathlib import Path

from proxy.server import ProxyServer
from proxy.bedrock import BedrockProxyServer
from runner.discovery import discover_benchmarks
from runner.executor import BenchmarkExecutor


async def run_benchmarks(args):
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    if args.bedrock:
        proxy = BedrockProxyServer(port=args.port, log_dir=log_dir)
    else:
        proxy = ProxyServer(port=args.port, log_dir=log_dir)
    runner = await proxy.start()
    print(f"Proxy started on http://127.0.0.1:{args.port} ({'bedrock' if args.bedrock else 'direct'})")

    swebench_ids = args.swebench_ids.split(",") if args.swebench_ids else None
    benchmarks = discover_benchmarks(
        filter_name=args.benchmark,
        swebench_limit=args.swebench_limit,
        swebench_ids=swebench_ids,
    )
    if not benchmarks:
        print("No benchmarks found.")
        await runner.cleanup()
        return

    print(f"Discovered {len(benchmarks)} benchmark(s):")
    for b in benchmarks:
        print(f"  - {b.name} ({b.benchmark_type})")
    print()

    executor = BenchmarkExecutor(
        proxy_port=args.port, log_dir=log_dir, model=args.model, use_bedrock=args.bedrock
    )
    results = []

    for benchmark in benchmarks:
        print(f"Running: {benchmark.name}...", flush=True)
        result = await executor.run_benchmark(benchmark)
        results.append(result)
        score_str = f"{result.score:.2f}" if result.score is not None else "n/a"
        print(f"  Done. Score: {score_str} | Session: {result.session_id}")
    print()

    print("=" * 60)
    print(f"{'Benchmark':<30} {'Type':<8} {'Score':<8} {'Session ID'}")
    print("-" * 60)
    for r in results:
        b = next((b for b in benchmarks if b.name == r.benchmark_name), None)
        btype = b.benchmark_type if b else "?"
        score_str = f"{r.score:.2f}" if r.score is not None else "n/a"
        print(f"{r.benchmark_name:<30} {btype:<8} {score_str:<8} {r.session_id}")
    print("=" * 60)

    await runner.cleanup()


async def run_viz(args):
    from viz.server import VizServer

    log_dir = Path(args.log_dir)
    viz = VizServer(log_dir=log_dir, port=args.viz_port)
    runner = await viz.start()
    print(f"Dashboard running at http://127.0.0.1:{args.viz_port}")
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        await runner.cleanup()


async def run_all(args):
    await run_benchmarks(args)
    print(f"\nStarting visualization dashboard on port {args.viz_port}...")
    await run_viz(args)


def main():
    parser = argparse.ArgumentParser(description="Claude Code Benchmarking & API Logger")
    parser.add_argument("--port", type=int, default=8080, help="Proxy server port")
    parser.add_argument("--viz-port", type=int, default=8090, help="Viz dashboard port")
    parser.add_argument("--log-dir", default="logs", help="Log output directory")
    parser.add_argument("--benchmark", type=str, default=None, help="Filter by benchmark name")
    parser.add_argument("--swebench-limit", type=int, default=None, help="Limit number of SWE-bench instances")
    parser.add_argument("--swebench-ids", type=str, default=None, help="Comma-separated SWE-bench instance IDs")
    parser.add_argument("--model", type=str, default=None, help="Model to use for benchmarks (e.g. sonnet)")
    parser.add_argument("--bedrock", action="store_true", help="Use Bedrock proxy (no API key needed)")
    parser.add_argument("--viz-only", action="store_true", help="Only start visualization server")
    parser.add_argument("--no-viz", action="store_true", help="Run benchmarks without starting dashboard after")

    args = parser.parse_args()

    if args.viz_only:
        asyncio.run(run_viz(args))
    elif args.no_viz:
        asyncio.run(run_benchmarks(args))
    else:
        asyncio.run(run_all(args))


if __name__ == "__main__":
    main()
