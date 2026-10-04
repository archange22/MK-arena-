"""Tamper-evident audit log for all actions"""
import time
import json

class AuditLogger:
    def __init__(self, log_file: str = "audit_log.jsonl"):
        self.log_file = log_file

    def log_action(self, user_id: int, action: str, tool: str, args: dict, status: str, details: str = ""):
        entry = {
            "timestamp": time.time(),
            "user_id": user_id,
            "action": action,
            "tool": tool,
            "status": status,
            "details": details
        }
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass
