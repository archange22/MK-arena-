"""Générateur de code et de tests pour NOVA."""

from typing import Dict, Any, Optional


class CodeGenerator:
    """Génère du code propre et des tests unitaires standardisés."""

    def generate_function(self, name: str, args: list, docstring: str, body: str = "pass") -> str:
        args_str = ", ".join(args)
        return (
            f"def {name}({args_str}):\n"
            f'    """{docstring}"""\n'
            f"    {body}\n"
        )

    def generate_class(self, name: str, methods: list, docstring: str) -> str:
        code = f"class {name}:\n"
        code += f'    """{docstring}"""\n\n'
        for m in methods:
            m_code = self.generate_function(m["name"], ["self"] + m.get("args", []), m.get("doc", ""), m.get("body", "pass"))
            indented = "\n".join("    " + line if line else "" for line in m_code.splitlines())
            code += indented + "\n\n"
        return code.strip() + "\n"

    def generate_unit_test(self, module_name: str, function_or_class: str, assertions: list) -> str:
        """Génère un fichier de test pytest."""
        code = f'"""Test pour {function_or_class} généré par NOVA."""\n\n'
        code += f"import pytest\n"
        code += f"from {module_name} import {function_or_class}\n\n\n"
        code += f"def test_{function_or_class.lower()}_basic():\n"
        for assertion in assertions:
            code += f"    assert {assertion}\n"
        return code
