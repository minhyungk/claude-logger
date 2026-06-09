from typing import Optional

from ...base import Benchmark
from .benchmark import InterCodeBenchmark

DATASET_NAME = "intercode/intercode"
DATASET_SPLIT = "test"


def discover_intercode_benchmarks(
    limit: Optional[int] = None,
    task_ids: Optional[list[str]] = None,
    task_type: Optional[str] = None,  # bash, python, sql
) -> list[Benchmark]:
    try:
        from datasets import load_dataset
    except ImportError:
        return []

    try:
        # InterCode has multiple subsets (bash, python, sql)
        config = task_type if task_type else "bash"
        dataset = load_dataset(DATASET_NAME, config, split=DATASET_SPLIT)
    except Exception:
        return []

    benchmarks: list[Benchmark] = []
    for idx, row in enumerate(dataset):
        task_id = row.get("task_id", f"task_{idx}")
        if task_ids and task_id not in task_ids:
            continue
        benchmarks.append(InterCodeBenchmark(task_id=task_id, task_data=dict(row)))
        if limit and len(benchmarks) >= limit:
            break

    return benchmarks
