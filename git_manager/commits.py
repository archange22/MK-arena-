"""Standardized Git commit authoring"""
import subprocess

class CommitManager:
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def commit(self, message: str, author: str = "NOVA Agent <nova@mkarena.local>") -> bool:
        subprocess.run(["git", "add", "-A"], cwd=self.repo_path, capture_output=True)
        res = subprocess.run(
            ["git", "commit", f"--author={author}", "-m", message],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        return res.returncode == 0
