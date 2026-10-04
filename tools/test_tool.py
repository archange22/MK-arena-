"""Pytest execution tool"""
import subprocess

class TestTool:
    def __init__(self, repo_dir: str):
        self.repo_dir = repo_dir

    def run_pytest(self, test_path: str = "tests") -> dict:
        res = subprocess.run(["pytest", test_path, "-q"], cwd=self.repo_dir, capture_output=True, text=True)
        return {"passed": res.returncode == 0, "output": res.stdout + res.stderr}
