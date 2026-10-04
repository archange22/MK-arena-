"""Memory expiration, decay and forgetting mechanism"""
import time

class ForgettingEngine:
    def __init__(self, default_ttl: int = 86400 * 7):
        self.default_ttl = default_ttl

    def is_expired(self, timestamp: float, importance: float = 1.0) -> bool:
        # High importance items decay much slower
        effective_ttl = self.default_ttl * max(importance, 0.1)
        return (time.time() - timestamp) > effective_ttl
