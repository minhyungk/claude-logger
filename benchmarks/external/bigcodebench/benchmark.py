import json
import subprocess
from pathlib import Path
from typing import Optional

from ...base import Benchmark


class BigCodeBenchBenchmark(Benchmark):
    def __init__(self, task_id: str, task_data: dict):
        self._task_id = task_id
        self._data = task_data
        self._work_dir: Optional[Path] = None

    @property
    def name(self) -> str:
        return f"bigcodebench-{self._task_id}"

    @property
    def benchmark_type(self) -> str:
        return "scored"

    def get_prompt(self) -> str:
        instruction = self._data.get("instruct_prompt", "") or self._data.get("instruction", "")
        code_context = self._data.get("code_context", "")

        prompt = f"""Complete the following coding task.

## Task
{instruction}
"""
        if code_context:
            prompt += f"""
## Code Context
```python
{code_context}
```
"""
        prompt += """
Please implement the required function or solve the problem.
"""
        return prompt

    def get_working_directory(self) -> Optional[Path]:
        return self._work_dir

    def setup(self, workspace_base: Optional[Path] = None) -> None:
        if workspace_base:
            bigcodebench_workspaces = workspace_base / "bigcodebench_workspaces"
            bigcodebench_workspaces.mkdir(parents=True, exist_ok=True)
            self._work_dir = bigcodebench_workspaces / self._task_id.replace("/", "_")
            self._work_dir.mkdir(parents=True, exist_ok=True)
        else:
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix=f"bigcodebench_{self._task_id}_")
            self._work_dir = Path(temp_dir)

        # Create initial Python file if starter code exists
        if self._work_dir:
            starter_code = self._data.get("code_context", "")
            if starter_code:
                (self._work_dir / "solution.py").write_text(starter_code)

    def score(self, session_dir: Path) -> Optional[float]:
        # BigCodeBench scoring requires running test cases
        # For now, return None to indicate manual scoring needed
        return None

    def cleanup(self) -> None:
        # Only cleanup if using temporary directory (not workspace)
        if self._work_dir and not str(self._work_dir).endswith("_workspaces"):
            import shutil
            shutil.rmtree(self._work_dir, ignore_errors=True)
