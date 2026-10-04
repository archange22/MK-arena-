"""Validation et sécurité du code pour NOVA."""

import ast
from typing import List, Tuple

PROTECTED_PATHS = {
    "security/",
    "main.py",
    ".env",
    ".env.example",
    "security/permissions.py",
    "security/antiraid.py",
}

FORBIDDEN_PATTERNS = [
    "rm -rf",
    "shutil.rmtree('/')",
    "os.system('rm",
    "eval(",
    "exec(",
    "__import__('os').system",
    "token.txt",
    "DISCORD_TOKEN",
]


class CodeValidator:
    """Valide les modifications de code avant exécution ou écriture."""

    def __init__(self, protected_paths: set = None):
        self.protected_paths = protected_paths or PROTECTED_PATHS

    def is_path_protected(self, file_path: str) -> bool:
        normalized = file_path.replace("\\", "/").lstrip("./")
        for prot in self.protected_paths:
            if normalized == prot or normalized.startswith(prot):
                return True
        return False

    def validate_syntax(self, code_content: str) -> Tuple[bool, str]:
        """Vérifie la syntaxe Python via ast.parse."""
        try:
            ast.parse(code_content)
            return True, "Syntaxe Python valide."
        except SyntaxError as e:
            return False, f"Erreur de syntaxe ligne {e.lineno}: {e.msg}"

    def check_forbidden_patterns(self, code_content: str) -> Tuple[bool, List[str]]:
        """Détecte des motifs dangereux ou destructeurs."""
        detected = []
        for pat in FORBIDDEN_PATTERNS:
            if pat in code_content:
                detected.append(pat)
        if detected:
            return False, detected
        return True, []

    def validate_change(self, file_path: str, code_content: str) -> Tuple[bool, str]:
        """Effectue l'ensemble des contrôles de sécurité."""
        if self.is_path_protected(file_path):
            return False, f"Modification refusée : '{file_path}' est un fichier système protégé."

        valid_syntax, syn_msg = self.validate_syntax(code_content)
        if not valid_syntax:
            return False, syn_msg

        safe, patterns = self.check_forbidden_patterns(code_content)
        if not safe:
            return False, f"Modification refusée : motifs dangereux détectés ({', '.join(patterns)})."

        return True, "Code validé et sécurisé."
