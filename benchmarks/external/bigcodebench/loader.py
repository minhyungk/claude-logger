from typing import Optional

from ...base import Benchmark
from .benchmark import BigCodeBenchBenchmark

DATASET_NAME = "bigcode/bigcodebench"
DATASET_SPLIT = "v0.1.4"


def discover_bigcodebench_benchmarks(
    limit: Optional[int] = None,
    task_ids: Optional[list[str]] = None,
) -> list[Benchmark]:
    try:
        from datasets import load_dataset
    except ImportError:
        return []

    try:
        dataset = load_dataset(DATASET_NAME, split=DATASET_SPLIT)
    except Exception:
        return []

    benchmarks: list[Benchmark] = []
    for idx, row in enumerate(dataset):
        task_id = row.get("task_id", f"task_{idx}")
        if task_ids and task_id not in task_ids:
            continue
        benchmarks.append(BigCodeBenchBenchmark(task_id=task_id, task_data=dict(row)))
        if limit and len(benchmarks) >= limit:
            break

    return benchmarks
