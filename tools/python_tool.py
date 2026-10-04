"""Sandboxed Python code runner"""
import ast

class PythonTool:
    @staticmethod
    def validate_syntax(code: str) -> bool:
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
