"""Journal d'historique des versions et modifications de NOVA."""

import json
import os
import time
from typing import List, Dict, Any


class ImprovementHistory:
    """Trace chaque modification et version appliquée avec succès."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def record(self, version: str, goal: str, files_modified: List[str], test_summary: str, author: str = "NOVA Autonomous Loop") -> Dict[str, Any]:
        entry = {
            "version": version,
            "goal": goal,
            "files_modified": files_modified,
            "test_summary": test_summary,
            "author": author,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.append(entry)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return entry

    def get_latest(self) -> Dict[str, Any]:
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data[-1] if data else {}
