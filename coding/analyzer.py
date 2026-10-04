"""Analyseur de code AST et structure de projet pour NOVA."""

import ast
import os
from typing import Dict, List, Any


class CodeAnalyzer:
    """Analyse statique de fichiers Python et de la structure du projet."""

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)

    def scan_directory(self) -> Dict[str, Any]:
        """Scanne le répertoire du projet et liste les fichiers par catégorie."""
        summary = {"files": [], "total_python_files": 0, "modules": []}
        for root, dirs, files in os.walk(self.root_dir):
            # Ignorer git et venv
            dirs[:] = [d for d in dirs if d not in {".git", ".venv", "__pycache__", "venv", ".pytest_cache"}]
            rel_root = os.path.relpath(root, self.root_dir)
            for file in files:
                rel_path = os.path.normpath(os.path.join(rel_root, file))
                if rel_path.startswith("."):
                    continue
                summary["files"].append(rel_path)
                if file.endswith(".py"):
                    summary["total_python_files"] += 1
                    mod_name = rel_path.replace(os.sep, ".").removesuffix(".py")
                    summary["modules"].append(mod_name)
        return summary

    def analyze_file(self, rel_path: str) -> Dict[str, Any]:
        """Analyse en détail les classes, fonctions et imports d'un fichier."""
        full_path = os.path.join(self.root_dir, rel_path)
        if not os.path.isfile(full_path):
            return {"error": f"Fichier non trouvé: {rel_path}"}

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content)
        except Exception as e:
            return {"error": f"Erreur de parsing: {str(e)}"}

        classes = []
        functions = []
        imports = []

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                classes.append({"name": node.name, "methods": methods, "line": node.lineno})
            elif isinstance(node, ast.FunctionDef):
                functions.append({"name": node.name, "args": [a.arg for a in node.args.args], "line": node.lineno})
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")

        return {
            "path": rel_path,
            "classes": classes,
            "functions": functions,
            "imports": imports,
            "lines_of_code": len(content.splitlines()),
        }

    def find_symbol(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Recherche où est définie une classe ou une fonction dans le projet."""
        matches = []
        scan = self.scan_directory()
        for f in scan["files"]:
            if f.endswith(".py"):
                res = self.analyze_file(f)
                if "classes" in res:
                    for c in res["classes"]:
                        if c["name"] == symbol_name:
                            matches.append({"type": "class", "file": f, "line": c["line"]})
                        if symbol_name in c.get("methods", []):
                            matches.append({"type": "method", "class": c["name"], "file": f})
                if "functions" in res:
                    for fn in res["functions"]:
                        if fn["name"] == symbol_name:
                            matches.append({"type": "function", "file": f, "line": fn["line"]})
        return matches
