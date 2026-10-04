"""REST API endpoints for the Web Dashboard & Code Studio"""
import time
from typing import Dict, Any

class DashboardAPI:
    def __init__(self, nova_core=None):
        self.core = nova_core

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": "ONLINE",
            "version": "5.0.0-alpha",
            "uptime": 1234.5,
            "cpu_percent": 12.4,
            "memory_mb": 145.2,
            "active_model": "NOVA Local Neural & Code Agent",
            "timestamp": time.time()
        }

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "test_success_rate": 100.0,
            "tasks_completed": 18,
            "proposals_accepted": 7,
            "avg_latency_ms": 42.1
        }

    def get_tasks(self) -> list:
        return [
            {"id": "task-01", "goal": "Indexation tournois Discord", "status": "COMPLETED"},
            {"id": "task-02", "goal": "Auto-évaluation AST", "status": "COMPLETED"}
        ]

    def get_logs(self, limit: int = 20) -> list:
        return [
            {"timestamp": time.time(), "level": "INFO", "message": "NOVA Core initialisé"},
            {"timestamp": time.time(), "level": "INFO", "message": "Toutes les barrières de sécurité actives"}
        ]
