"""Git CLI invocation tool"""
import subprocess

class GitTool:
    def __init__(self, repo_dir: str):
        self.repo_dir = repo_dir

    def run_cmd(self, args: list) -> dict:
        res = subprocess.run(["git"] + args, cwd=self.repo_dir, capture_output=True, text=True)
        return {"code": res.returncode, "stdout": res.stdout, "stderr": res.stderr}
