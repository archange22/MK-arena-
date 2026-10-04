"""NOVA Lifecycle and state management"""
import time

class LifecycleManager:
    def __init__(self):
        self.started_at = time.time()
        self.status = "INITIALIZING"
        self.subsystems = {}

    def register_subsystem(self, name: str, instance):
        self.subsystems[name] = instance

    def set_status(self, status: str):
        self.status = status

    def uptime(self) -> float:
        return time.time() - self.started_at

    def health(self) -> dict:
        return {
            "status": self.status,
            "uptime_seconds": round(self.uptime(), 2),
            "subsystems_count": len(self.subsystems),
            "subsystems": list(self.subsystems.keys())
        }
