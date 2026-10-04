"""Environnement de test isolé (Sandbox) pour NOVA."""

import os
import shutil
import tempfile
from typing import Dict, Any, Callable
from coding.tester import CodeTester
from coding.editor import CodeEditor


class Sandbox:
    """Crée une copie temporaire complète du dépôt pour tester en toute sécurité."""

    def __init__(self, source_dir: str):
        self.source_dir = os.path.abspath(source_dir)
        self.temp_dir: str = ""

    def __enter__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="nova_sandbox_")
        # Copie récursive en ignorant venv et git lourd
        shutil.copytree(
            self.source_dir,
            self.temp_dir,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", "*.pyc", "NOVA_*.zip"),
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    @property
    def path(self) -> str:
        return self.temp_dir

    def test_modification(self, rel_path: str, new_content: str) -> Dict[str, Any]:
        """Applique une modification dans la sandbox et exécute les tests."""
        editor = CodeEditor(self.temp_dir)
        success, msg = editor.write_file(rel_path, new_content, bypass_protection=True)
        if not success:
            return {"success": False, "error": f"Échec d'écriture dans la sandbox: {msg}"}

        tester = CodeTester(self.temp_dir)
        results = tester.run_tests()
        return {
            "applied": True,
            "test_results": results,
            "safe_to_merge": results.get("success", False),
        }
