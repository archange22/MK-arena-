"""Éditeur de fichiers atomique et sécurisé pour NOVA."""

import os
import shutil
import tempfile
from typing import Tuple, Optional
from coding.validator import CodeValidator


class CodeEditor:
    """Gère l'écriture, la modification et la restauration de fichiers."""

    def __init__(self, root_dir: str, validator: Optional[CodeValidator] = None):
        self.root_dir = os.path.abspath(root_dir)
        self.validator = validator or CodeValidator()
        self.backups: dict = {}

    def _resolve_path(self, rel_path: str) -> str:
        return os.path.abspath(os.path.join(self.root_dir, rel_path))

    def write_file(self, rel_path: str, content: str, bypass_protection: bool = False) -> Tuple[bool, str]:
        """Écrit ou crée un fichier après validation de sécurité."""
        if not bypass_protection:
            valid, msg = self.validator.validate_change(rel_path, content)
            if not valid:
                return False, msg

        full_path = self._resolve_path(rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Sauvegarde pour rollback si le fichier existe
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                self.backups[rel_path] = f.read()

        # Écriture atomique
        dir_name = os.path.dirname(full_path)
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        shutil.move(tmp_path, full_path)
        return True, f"Fichier '{rel_path}' enregistré avec succès."

    def rollback(self, rel_path: str) -> Tuple[bool, str]:
        """Restaure la version précédente d'un fichier."""
        if rel_path not in self.backups:
            return False, f"Aucune sauvegarde disponible pour '{rel_path}'."

        full_path = self._resolve_path(rel_path)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(self.backups[rel_path])

        del self.backups[rel_path]
        return True, f"Fichier '{rel_path}' restauré à son état antérieur."

    def patch_line(self, rel_path: str, target: str, replacement: str) -> Tuple[bool, str]:
        """Remplace une ligne ou un motif textuel dans un fichier."""
        full_path = self._resolve_path(rel_path)
        if not os.path.exists(full_path):
            return False, f"Fichier '{rel_path}' introuvable."

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        if target not in content:
            return False, f"Cible '{target}' non trouvée dans {rel_path}."

        new_content = content.replace(target, replacement, 1)
        return self.write_file(rel_path, new_content)
