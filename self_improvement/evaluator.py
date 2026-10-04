"""Évaluateur de performance et de qualité de code pour NOVA."""

import time
from typing import Dict, Any
from coding.tester import CodeTester
from coding.analyzer import CodeAnalyzer


class SelfEvaluator:
    """Mesure la santé globale, le taux de réussite des tests et la couverture."""

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.tester = CodeTester(root_dir)
        self.analyzer = CodeAnalyzer(root_dir)

    def evaluate_health(self) -> Dict[str, Any]:
        start = time.time()
        test_res = self.tester.run_tests()
        duration = round(time.time() - start, 3)

        scan = self.analyzer.scan_directory()
        total_py = scan["total_python_files"]

        passed = test_res.get("passed", 0)
        failed = test_res.get("failed", 0)
        errors = test_res.get("errors", 0)
        total_tests = passed + failed + errors

        success_rate = (passed / total_tests * 100) if total_tests > 0 else 100.0

        return {
            "status": "HEALTHY" if test_res["success"] else "DEGRADED",
            "success_rate": round(success_rate, 2),
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "duration_seconds": duration,
            "python_files_count": total_py,
        }
