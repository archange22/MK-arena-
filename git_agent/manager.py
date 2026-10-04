"""Gestionnaire d'opérations Git pour NOVA."""

import subprocess
import os
from typing import Tuple, List, Dict, Any


class GitAgent:
    """Wrapper pour inspecter, brancher et commiter automatiquement."""

    def __init__(self, repo_dir: str):
        self.repo_dir = os.path.abspath(repo_dir)

    def _run_git(self, args: List[str]) -> Tuple[int, str, str]:
        res = subprocess.run(
            ["git"] + args,
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
        )
        return res.returncode, res.stdout.strip(), res.stderr.strip()

    def get_status(self) -> Dict[str, Any]:
        code, out, _ = self._run_git(["status", "--porcelain"])
        lines = out.splitlines() if out else []
        return {
            "is_clean": len(lines) == 0,
            "modified_files": [l.strip() for l in lines],
        }

    def current_branch(self) -> str:
        code, out, _ = self._run_git(["branch", "--show-current"])
        return out or "main"

    def create_branch(self, branch_name: str) -> Tuple[bool, str]:
        code, out, err = self._run_git(["checkout", "-b", branch_name])
        if code == 0:
            return True, f"Branche '{branch_name}' créée et activée."
        return False, err or out

    def checkout(self, branch_name: str) -> Tuple[bool, str]:
        code, out, err = self._run_git(["checkout", branch_name])
        return code == 0, err or out

    def commit_changes(self, message: str, files: List[str] = None) -> Tuple[bool, str]:
        """Ajoute et commite les changements avec signature NOVA."""
        if files:
            for f in files:
                self._run_git(["add", f])
        else:
            self._run_git(["add", "."])

        full_msg = f"[NOVA v2.0] {message}\n\nCo-authored-by: NOVA Self-Improving Agent <nova@mk-arena.local>"
        code, out, err = self._run_git(["commit", "-m", full_msg])
        if code == 0:
            return True, f"Commit validé : {message}"
        return False, err or out

    def get_diff(self) -> str:
        code, out, _ = self._run_git(["diff"])
        return out
