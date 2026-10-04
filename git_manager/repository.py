"""Git repository wrapper"""
import os
import subprocess

class GitRepository:
    def __init__(self, repo_path: str = "."):
        self.repo_path = os.path.abspath(repo_path)

    def current_branch(self) -> str:
        try:
            res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=self.repo_path, capture_output=True, text=True)
            return res.stdout.strip() or "main"
        except Exception:
            return "main"

    def status(self) -> dict:
        try:
            res = subprocess.run(["git", "status", "--porcelain"], cwd=self.repo_path, capture_output=True, text=True)
            changes = [l.strip() for l in res.stdout.splitlines() if l.strip()]
            return {"clean": len(changes) == 0, "changes": changes}
        except Exception:
            return {"clean": True, "changes": []}
