"""Synchronisation temps réel entre NOVA et Firebase Realtime Database."""

import json
import urllib.request
import urllib.error
import time
from typing import Dict, Any, Optional

FIREBASE_RTDB_URL = "https://mk-esports-events-default-rtdb.europe-west1.firebasedatabase.app"

class FirebaseSync:
    """Synchronise l'état du système, des missions et des alertes vers Firebase."""

    def __init__(self, database_url: str = FIREBASE_RTDB_URL):
        self.database_url = database_url.rstrip('/')

    def _put(self, path: str, data: Dict[str, Any]) -> bool:
        url = f"{self.database_url}/{path.lstrip('/')}.json"
        body = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=body, method='PUT')
        req.add_header('Content-Type', 'application/json')
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status in (200, 201)
        except Exception:
            return False

    def sync_status(self, uptime_seconds: float, active_model: str, mood: str, tests_passed: int, total_tests: int) -> bool:
        """Publie les métriques globales du bot."""
        payload = {
            "online": True,
            "version": "5.0.0",
            "uptime_seconds": uptime_seconds,
            "active_model": active_model,
            "mood": mood,
            "tests": {
                "passed": tests_passed,
                "total": total_tests,
                "success_rate": 100.0 if total_tests > 0 and tests_passed == total_tests else 0.0
            },
            "last_synced_at": time.time()
        }
        return self._put("nova/status", payload)

    def push_audit_log(self, level: str, message: str, source: str = "core") -> bool:
        """Envoie un événement de journal d'audit."""
        payload = {
            "timestamp": time.time(),
            "level": level,
            "message": message,
            "source": source
        }
        return self._put(f"nova/logs/{int(time.time() * 1000)}", payload)
