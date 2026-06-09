import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from ...base import Benchmark


class SWEBenchBenchmark(Benchmark):
    def __init__(self, instance_id: str, instance_data: dict):
        self._instance_id = instance_id
        self._data = instance_data
        self._work_dir: Optional[Path] = None
        self._temp_dir: Optional[str] = None

    @property
    def name(self) -> str:
        return f"swebench-{self._instance_id}"

    @property
    def benchmark_type(self) -> str:
        return "scored"

    @property
    def repo(self) -> str:
        return self._data.get("repo", "")

    @property
    def base_commit(self) -> str:
        return self._data.get("base_commit", "")

    @property
    def test_patch(self) -> str:
        return self._data.get("test_patch", "")

    @property
    def gold_patch(self) -> str:
        return self._data.get("patch", "")

    def get_prompt(self) -> str:
        problem = self._data.get("problem_statement", "")
        hints = self._data.get("hints_text", "")
        prompt = f"""Fix the following issue in the {self.repo} repository.

## Issue
{problem}
"""
        if hints:
            prompt += f"""
## Hints
{hints}
"""
        prompt += """
Please identify and fix the bug. Apply the fix directly to the repository files.
"""
        return prompt

    def get_working_directory(self) -> Optional[Path]:
        return self._work_dir

    def setup(self) -> None:
        self._temp_dir = tempfile.mkdtemp(prefix=f"swebench_{self._instance_id}_")
        self._work_dir = Path(self._temp_dir)

        repo_url = f"https://github.com/{self.repo}.git"
        subprocess.run(
            ["git", "clone", "--depth", "100", repo_url, str(self._work_dir)],
            capture_output=True,
            timeout=120,
        )
        subprocess.run(
            ["git", "checkout", self.base_commit],
            cwd=str(self._work_dir),
            capture_output=True,
            timeout=30,
        )

    def score(self, session_dir: Path) -> Optional[float]:
        if not self._work_dir or not self._work_dir.exists():
            return None
        if not self.test_patch:
            return None

        test_patch_file = self._work_dir / "_test_patch.diff"
        test_patch_file.write_text(self.test_patch)

        apply_result = subprocess.run(
            ["git", "apply", str(test_patch_file)],
            cwd=str(self._work_dir),
            capture_output=True,
            timeout=30,
        )
        if apply_result.returncode != 0:
            return 0.0

        test_cmd = self._data.get("test_cmd")
        if not test_cmd:
            return None

        test_result = subprocess.run(
            test_cmd,
            shell=True,
            cwd=str(self._work_dir),
            capture_output=True,
            timeout=300,
        )
        return 1.0 if test_result.returncode == 0 else 0.0

    def cleanup(self) -> None:
        if self._temp_dir:
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None
            self._work_dir = None
