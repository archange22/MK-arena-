"""Git branch management for isolated features"""
import subprocess

class BranchManager:
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def create_and_checkout(self, branch_name: str) -> bool:
        res = subprocess.run(["git", "checkout", "-b", branch_name], cwd=self.repo_path, capture_output=True, text=True)
        return res.returncode == 0
