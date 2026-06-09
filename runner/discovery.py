from pathlib import Path
from typing import Optional

from benchmarks.base import Benchmark
from benchmarks.open.loader import discover_open_benchmarks
from benchmarks.external.swebench import discover_swebench_benchmarks
from benchmarks.external.terminalbench import discover_terminalbench_benchmarks
from benchmarks.external.intercode import discover_intercode_benchmarks
from benchmarks.external.bigcodebench import discover_bigcodebench_benchmarks


def discover_benchmarks(
    base_dir: Path | None = None,
    filter_name: Optional[str] = None,
    filter_type: Optional[str] = None,
    swebench_limit: Optional[int] = None,
    swebench_ids: Optional[list[str]] = None,
    terminalbench_limit: Optional[int] = None,
    terminalbench_ids: Optional[list[str]] = None,
    intercode_limit: Optional[int] = None,
    intercode_ids: Optional[list[str]] = None,
    intercode_task_type: Optional[str] = None,
    bigcodebench_limit: Optional[int] = None,
    bigcodebench_ids: Optional[list[str]] = None,
) -> list[Benchmark]:
    if base_dir is None:
        base_dir = Path(__file__).parent.parent / "benchmarks"

    benchmarks: list[Benchmark] = []

    # Load open benchmarks only if not filtered out
    if filter_type is None or filter_type == "open":
        open_dir = base_dir / "open"
        if open_dir.exists():
            benchmarks.extend(discover_open_benchmarks(open_dir))

    # Load swebench benchmarks only if not filtered out
    if filter_type is None or filter_type == "swebench":
        benchmarks.extend(
            discover_swebench_benchmarks(limit=swebench_limit, instance_ids=swebench_ids)
        )

    # Load terminalbench benchmarks only if not filtered out
    if filter_type is None or filter_type == "terminalbench":
        benchmarks.extend(
            discover_terminalbench_benchmarks(limit=terminalbench_limit, task_ids=terminalbench_ids)
        )

    # Load intercode benchmarks only if not filtered out
    if filter_type is None or filter_type == "intercode":
        benchmarks.extend(
            discover_intercode_benchmarks(
                limit=intercode_limit, task_ids=intercode_ids, task_type=intercode_task_type
            )
        )

    # Load bigcodebench benchmarks only if not filtered out
    if filter_type is None or filter_type == "bigcodebench":
        benchmarks.extend(
            discover_bigcodebench_benchmarks(limit=bigcodebench_limit, task_ids=bigcodebench_ids)
        )

    if filter_name:
        benchmarks = [b for b in benchmarks if filter_name in b.name]

    return benchmarks
