"""Filesystem access tool (restricted to project root)"""
import os

class FilesystemTool:
    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)

    def read_file(self, rel_path: str) -> str:
        target = os.path.abspath(os.path.join(self.root_dir, rel_path))
        if not target.startswith(self.root_dir):
            raise PermissionError("Path traversal interdit.")
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def list_dir(self, rel_path: str = ".") -> list:
        target = os.path.abspath(os.path.join(self.root_dir, rel_path))
        return os.listdir(target)
