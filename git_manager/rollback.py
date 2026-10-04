"""Rollback and recovery to safe commit"""
import subprocess

class GitRollback:
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def rollback_hard(self, commit_sha: str = "HEAD~1") -> bool:
        res = subprocess.run(["git", "reset", "--hard", commit_sha], cwd=self.repo_path, capture_output=True, text=True)
        return res.returncode == 0
