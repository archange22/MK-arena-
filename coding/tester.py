"""Exécuteur de tests automatisés pour NOVA."""

import subprocess
import os
import re
from typing import Dict, Any


class CodeTester:
    """Exécute pytest ou unittest et formate le bilan d'évaluation."""

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)

    def run_tests(self, target_path: str = None, timeout: int = 45) -> Dict[str, Any]:
        """Lance pytest et analyse le résultat."""
        cmd = ["pytest", "-q"]
        if target_path:
            cmd.append(target_path)

        try:
            proc = subprocess.run(
                cmd,
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            stdout = proc.stdout
            stderr = proc.stderr
            exit_code = proc.returncode

            # Analyse des résultats
            passed = 0
            failed = 0
            errors = 0

            pass_match = re.search(r"(\d+)\s+passed", stdout)
            fail_match = re.search(r"(\d+)\s+failed", stdout)
            err_match = re.search(r"(\d+)\s+error", stdout)

            if pass_match:
                passed = int(pass_match.group(1))
            if fail_match:
                failed = int(fail_match.group(1))
            if err_match:
                errors = int(err_match.group(1))

            success = (exit_code == 0)

            return {
                "success": success,
                "exit_code": exit_code,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "stdout": stdout,
                "stderr": stderr,
                "summary": f"{passed} passed, {failed} failed, {errors} errors",
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "error": "Timeout dépassé lors de l'exécution des tests.",
                "summary": "Timeout",
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "error": str(e),
                "summary": "Erreur d'exécution",
            }
