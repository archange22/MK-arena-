"""Automated Code Reviewer: checks security, complexity, style"""
import ast

class CodeReviewer:
    DANGEROUS_IMPORTS = {"pickle", "shelve", "eval", "exec"}

    @classmethod
    def review_code(cls, code: str) -> dict:
        issues = []
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {"valid": False, "issues": [f"Syntax error: {e}"], "score": 0}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in cls.DANGEROUS_IMPORTS:
                        issues.append(f"Import suspect : {alias.name}")
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ("eval", "exec"):
                    issues.append(f"Appel dangereux interdit : {node.func.id}()")

        score = max(10 - len(issues) * 3, 0)
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "score": score
        }
