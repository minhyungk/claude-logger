import json
from pathlib import Path
from typing import Optional

from ..base import Benchmark


class OpenBenchmark(Benchmark):
    def __init__(self, json_path: Path):
        with open(json_path) as f:
            self._data = json.load(f)
        self._path = json_path

    @property
    def name(self) -> str:
        return self._data.get("name", self._path.stem)

    @property
    def benchmark_type(self) -> str:
        return "open"

    def get_prompt(self) -> str:
        return self._data["prompt"]

    def get_claude_args(self) -> list[str]:
        return self._data.get("claude_args", [])

    def get_working_directory(self) -> Optional[Path]:
        wd = self._data.get("working_directory")
        if wd:
            return Path(wd)
        return None


def discover_open_benchmarks(directory: Path | None = None) -> list[Benchmark]:
    if directory is None:
        directory = Path(__file__).parent
    benchmarks = []
    for json_file in sorted(directory.glob("*.json")):
        benchmarks.append(OpenBenchmark(json_file))
    return benchmarks
