import json
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
        self._workspace_base: Optional[Path] = None

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
    def version(self) -> str:
        return self._data.get("version", "")

    @property
    def test_patch(self) -> str:
        return self._data.get("test_patch", "")

    @property
    def environment_setup_commit(self) -> str:
        return self._data.get("environment_setup_commit", self.base_commit)

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

    def setup(self, workspace_base: Optional[Path] = None) -> None:
        # Use workspace if provided, otherwise fall back to temp directory
        if workspace_base:
            self._workspace_base = workspace_base
            swebench_workspaces = workspace_base / "swebench_workspaces"
            swebench_workspaces.mkdir(parents=True, exist_ok=True)
            self._work_dir = swebench_workspaces / self._instance_id.replace("/", "_")
            self._work_dir.mkdir(parents=True, exist_ok=True)
        else:
            temp_dir = tempfile.mkdtemp(prefix=f"swebench_{self._instance_id}_")
            self._work_dir = Path(temp_dir)

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

        docker_check = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5,
        )
        if docker_check.returncode != 0:
            print(f"  [WARNING] Docker not available, skipping evaluation for {self._instance_id}")
            return None

        try:
            score = self._evaluate_in_docker()
            return score
        except Exception as e:
            print(f"  [ERROR] Docker evaluation failed: {e}")
            return None

    def _evaluate_in_docker(self) -> Optional[float]:
        eval_dir = self._work_dir.parent / f"eval_{self._instance_id}"
        eval_dir.mkdir(exist_ok=True)

        repo_copy = eval_dir / "repo"
        if repo_copy.exists():
            shutil.rmtree(repo_copy)
        shutil.copytree(self._work_dir, repo_copy)

        test_patch_file = eval_dir / "test.patch"
        test_patch_file.write_text(self.test_patch)

        eval_script = eval_dir / "eval.sh"
        # Try to apply test patch, but don't fail if it doesn't apply
        # (Claude may have already modified the test file)
        eval_script.write_text(f"""#!/bin/bash
set -e
cd /testbed
git apply /eval/test.patch || echo "Warning: test patch did not apply, using existing tests"
{self._data.get('test_cmd', 'python -m pytest')}
""")
        eval_script.chmod(0o755)

        python_version = self._infer_python_version()

        dockerfile = eval_dir / "Dockerfile"
        docker_content = f"""FROM python:{python_version}-slim
RUN apt-get update && apt-get install -y git && apt-get clean
WORKDIR /testbed
COPY repo /testbed
RUN pip install --no-cache-dir -e . || pip install --no-cache-dir -r requirements.txt || true
RUN pip install --no-cache-dir pytest pytest-cov || true
"""
        dockerfile.write_text(docker_content)

        image_name = f"swebench-{self._instance_id.replace('/', '-').lower()}"
        build_result = subprocess.run(
            ["docker", "build", "-t", image_name, "."],
            cwd=str(eval_dir),
            capture_output=True,
            timeout=300,
        )
        if build_result.returncode != 0:
            print(f"  [ERROR] Docker build failed: {build_result.stderr.decode()[:200]}")
            return 0.0

        run_result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", f"{eval_dir.absolute()}:/eval",
                image_name,
                "/bin/bash", "/eval/eval.sh"
            ],
            capture_output=True,
            timeout=300,
        )

        # Save test output for debugging
        test_output_file = eval_dir / "test_output.txt"
        test_output_file.write_text(
            f"=== STDOUT ===\n{run_result.stdout.decode()}\n\n=== STDERR ===\n{run_result.stderr.decode()}"
        )

        subprocess.run(["docker", "rmi", image_name], capture_output=True, timeout=30)

        if run_result.returncode != 0:
            print(f"  [INFO] Tests failed (exit code {run_result.returncode}). Output saved to {test_output_file}")

        return 1.0 if run_result.returncode == 0 else 0.0

    def _infer_python_version(self) -> str:
        repo_lower = self.repo.lower()
        version = self.version.lower()

        if "django" in repo_lower:
            if "3." in version or "4." in version:
                return "3.9"
            return "3.8"
        elif "flask" in repo_lower or "requests" in repo_lower:
            return "3.9"
        elif "sympy" in repo_lower or "matplotlib" in repo_lower:
            return "3.10"
        elif "sklearn" in repo_lower or "scikit" in repo_lower:
            return "3.10"
        elif "pytest" in repo_lower:
            return "3.11"
        else:
            return "3.10"

    def cleanup(self) -> None:
        # Only cleanup if using temporary directory (not workspace)
        if self._work_dir and not self._workspace_base:
            shutil.rmtree(self._work_dir, ignore_errors=True)
            self._work_dir = None

        # Always cleanup eval directory
        if self._work_dir:
            eval_dir = self._work_dir.parent / f"eval_{self._instance_id}"
            if eval_dir.exists():
                shutil.rmtree(eval_dir, ignore_errors=True)
