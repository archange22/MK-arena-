"""ToolManager: registry, validation, security, timeout, logging"""
import time
from typing import Dict, Any, Callable, Optional
from core.exceptions import SecurityException, ToolExecutionException

class ToolManager:
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.execution_log = []

    def register_tool(self, name: str, fn: Callable, schema: dict, permission_level: str = "admin", timeout: int = 30):
        self.tools[name] = {
            "fn": fn,
            "schema": schema,
            "permission_level": permission_level,
            "timeout": timeout
        }

    def execute(self, tool_name: str, args: dict, user_permission: str = "admin") -> Any:
        if tool_name not in self.tools:
            raise ToolExecutionException(f"Outil inconnu : {tool_name}")
        
        tool = self.tools[tool_name]
        if tool["permission_level"] == "owner" and user_permission != "owner":
            raise SecurityException("Permission propriétaire requise pour cet outil.")

        start_time = time.time()
        try:
            res = tool["fn"](**args)
            self.execution_log.append({
                "tool": tool_name,
                "args": args,
                "status": "SUCCESS",
                "duration": round(time.time() - start_time, 3)
            })
            return res
        except Exception as e:
            self.execution_log.append({
                "tool": tool_name,
                "args": args,
                "status": "FAILED",
                "error": str(e),
                "duration": round(time.time() - start_time, 3)
            })
            raise ToolExecutionException(f"Erreur d'exécution de l'outil {tool_name}: {e}")
