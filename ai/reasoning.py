"""Moteur de raisonnement avancé et d'analyse d'erreurs pour NOVA (v5.0)."""

import re
from typing import Dict, Any, List, Optional


class ReasoningEngine:
    """Analyse les échecs de tests, formule des hypothèses de correction et enrichit les réponses techniques."""

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

        if "AssertionError" in combined:
            diagnosis["error_type"] = "AssertionError"
            diagnosis["suggested_fix"] = "Vérifier la valeur de retour ou assouplir la condition de validation."
        elif "SyntaxError" in combined:
            diagnosis["error_type"] = "SyntaxError"
            diagnosis["suggested_fix"] = "Corriger la syntaxe Python au niveau de la ligne signalée."
        elif "NameError" in combined:
            diagnosis["error_type"] = "NameError"
            diagnosis["suggested_fix"] = "Vérifier l'importation de la variable ou fonction manquante."
        elif "TypeError" in combined:
            diagnosis["error_type"] = "TypeError"
            diagnosis["suggested_fix"] = "Contrôler les arguments passés et leur typage."
        elif "ModuleNotFoundError" in combined or "ImportError" in combined:
            diagnosis["error_type"] = "ImportError"
            diagnosis["suggested_fix"] = "Installer le paquet manquant ou corriger le chemin d'import relatif."

        file_match = re.search(r"([a-zA-Z0-9_\/\.-]+\.py):(\d+):", combined)
        if file_match:
            diagnosis["failed_file"] = file_match.group(1)
            diagnosis["failed_line"] = int(file_match.group(2))

        lines = [line.strip() for line in combined.splitlines() if line.strip()]
        for line in reversed(lines):
            if any(err in line for err in ("Error:", "FAILED", "AssertionError", "Exception:")):
                diagnosis["error_message"] = line
                break

        return diagnosis

    def build_chain_of_thought(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """Génère un plan de raisonnement multi-étapes pour répondre avec la plus haute précision."""
        steps = [
            {"step": "Analyse du besoin", "action": f"Identifier les contraintes clés dans : '{prompt[:80]}...'"},
            {"step": "Recherche contextuelle", "action": "Vérifier la mémoire sémantique et les règles MK Arena associées."},
            {"step": "Génération & Vérification", "action": "Construire la solution et valider sa cohérence et sa sécurité."},
            {"step": "Formatage de sortie", "action": "Présenter une réponse claire, typée et directement actionnable."}
        ]
        return steps

    def get_codm_tournament_strategy(self, mode: str, map_name: str) -> Dict[str, Any]:
        """Fournit une expertise tactique pointue pour les tournois MK Arena CODM."""
        mode_upper = mode.upper()
        map_lower = map_name.lower()

        strategies = {
            "HARDPOINT": {
                "general": "Contrôle des rotations à T-20s, ancrage (Anchor) sur le point de spawn avantageux.",
                "maps": {
                    "standoff": "P1 Cour centrale, P2 Bâtiment briques (Anchor arrière station), P3 Maison verte.",
                    "raid": "P1 Cour centrale, P2 Garage/Basketball, P3 Salon du bas, P4 Piscine.",
                    "summit": "P1 Salle de contrôle (Point clé), P2 Bâtiment 2 (Spawn Helipad), P3 Pente."
                }
            },
            "SND": {
                "general": "Gestion de l'économie d'utilitaires (fumigènes/trophies), trade frag obligatoire en ouverture.",
                "maps": {
                    "standoff": "Site A privilégié pour pose rapide avec fumigène; Site B sous contrôle sniper.",
                    "raid": "Site A au niveau de la terrasse/statue, Site B via la cuisine/chambre.",
                    "slums": "Contrôle du mid bleu indispensable pour couper les rotations adverses."
                }
            }
        }

        mode_data = strategies.get(mode_upper, strategies["HARDPOINT"])
        map_advice = mode_data["maps"].get(map_lower, "Maintenir les lignes croisées et surveiller les flankers.")

        return {
            "mode": mode_upper,
            "map": map_name,
            "tactique": mode_data["general"],
            "conseil_carte": map_advice,
            "weapons_meta": ["Krig 6", "CBR4", "DL Q33", "Holger 26", "Switchblade X9"]
        }
