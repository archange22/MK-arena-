"""File patcher: apply diffs and line replacements safely"""
import difflib

class CodePatcher:
    @staticmethod
    def create_diff(original: str, modified: str, filename: str = "file.py") -> str:
        orig_lines = original.splitlines(keepends=True)
        mod_lines = modified.splitlines(keepends=True)
        diff = difflib.unified_diff(orig_lines, mod_lines, fromfile=f"a/{filename}", tofile=f"b/{filename}")
        return "".join(diff)

    @staticmethod
    def apply_patch(original: str, search_block: str, replace_block: str) -> str:
        if search_block not in original:
            raise ValueError("Le bloc cible n'a pas été trouvé dans le fichier d'origine.")
        return original.replace(search_block, replace_block, 1)
