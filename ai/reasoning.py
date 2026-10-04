"""Moteur de raisonnement et d'analyse d'erreurs pour NOVA."""

import re
from typing import Dict, Any, List


class ReasoningEngine:
    """Analyse les échecs de tests et formule des hypothèses de correction."""

    def analyze_test_failure(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Extrait les fichiers, lignes et exceptions d'un échec pytest."""
        combined = stdout + "\n" + stderr
        diagnosis = {
            "error_type": "Unknown",
            "failed_file": None,
            "failed_line": None,
            "error_message": "",
            "suggested_fix": "",
        }

        # Détection d'erreurs courantes
        if "AssertionError" in combined:
            diagnosis["error_type"] = "AssertionError"
            diagnosis["suggested_fix"] = "Vérifier la valeur de retour ou assouplir la condition de validation."
        elif "SyntaxError" in combined:
            diagnosis["error_type"] = "SyntaxError"
            diagnosis["suggested_fix"] = "Corriger la syntaxe Python (parenthèses, indentation, deux-points)."
        elif "NameError" in combined or "AttributeError" in combined:
            diagnosis["error_type"] = "NameOrAttributeError"
            diagnosis["suggested_fix"] = "Vérifier les imports et la conformité des noms d'attributs/méthodes."
        elif "ModuleNotFoundError" in combined:
            diagnosis["error_type"] = "ModuleNotFoundError"
            diagnosis["suggested_fix"] = "Vérifier le PYTHONPATH ou installer la dépendance manquante."

        # Extraction de la ligne et du fichier
        file_match = re.search(r"([\w_/-]+\.py):(\d+):", combined)
        if file_match:
            diagnosis["failed_file"] = file_match.group(1)
            diagnosis["failed_line"] = int(file_match.group(2))

        # Extraction de la ligne d'erreur
        err_lines = [l.strip() for l in combined.splitlines() if l.strip().startswith("E   ")]
        if err_lines:
            diagnosis["error_message"] = " ".join(err_lines)

        return diagnosis
