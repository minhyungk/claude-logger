import json
import subprocess
from pathlib import Path
from typing import Optional

from ...base import Benchmark


class TerminalBenchBenchmark(Benchmark):
    def __init__(self, task_id: str, task_data: dict):
        self._task_id = task_id
        self._data = task_data
        self._work_dir: Optional[Path] = None

    @property
    def name(self) -> str:
        return f"terminalbench-{self._task_id}"

    @property
    def benchmark_type(self) -> str:
        return "scored"

    def get_prompt(self) -> str:
        instruction = self._data.get("instruction", "")
        context = self._data.get("context", "")

        prompt = f"""Complete the following terminal task.

## Task
{instruction}
"""
        if context:
            prompt += f"""
## Context
{context}
"""
        prompt += """
Please execute the necessary terminal commands to complete this task.
"""
        return prompt

    def get_working_directory(self) -> Optional[Path]:
        return self._work_dir

    def setup(self, workspace_base: Optional[Path] = None) -> None:
        if workspace_base:
            terminalbench_workspaces = workspace_base / "terminalbench_workspaces"
            terminalbench_workspaces.mkdir(parents=True, exist_ok=True)
            self._work_dir = terminalbench_workspaces / self._task_id.replace("/", "_")
            self._work_dir.mkdir(parents=True, exist_ok=True)
        else:
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix=f"terminalbench_{self._task_id}_")
            self._work_dir = Path(temp_dir)

    def score(self, session_dir: Path) -> Optional[float]:
        # TerminalBench scoring would require checking command execution results
        # For now, return None to indicate manual scoring needed
        return None

    def cleanup(self) -> None:
        # Only cleanup if using temporary directory (not workspace)
        if self._work_dir and not str(self._work_dir).endswith("_workspaces"):
            import shutil
            shutil.rmtree(self._work_dir, ignore_errors=True)
