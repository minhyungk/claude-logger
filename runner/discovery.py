from pathlib import Path
from typing import Optional

from benchmarks.base import Benchmark
from benchmarks.open.loader import discover_open_benchmarks
from benchmarks.external.swebench import discover_swebench_benchmarks


def discover_benchmarks(
    base_dir: Path | None = None,
    filter_name: Optional[str] = None,
    filter_type: Optional[str] = None,
    swebench_limit: Optional[int] = None,
    swebench_ids: Optional[list[str]] = None,
) -> list[Benchmark]:
    if base_dir is None:
        base_dir = Path(__file__).parent.parent / "benchmarks"

    benchmarks: list[Benchmark] = []

    open_dir = base_dir / "open"
    if open_dir.exists():
        benchmarks.extend(discover_open_benchmarks(open_dir))

    benchmarks.extend(
        discover_swebench_benchmarks(limit=swebench_limit, instance_ids=swebench_ids)
    )

    if filter_name:
        benchmarks = [b for b in benchmarks if filter_name in b.name]

    if filter_type:
        benchmarks = [b for b in benchmarks if b.benchmark_type == filter_type]

    return benchmarks
