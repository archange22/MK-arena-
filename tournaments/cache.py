"""Fast in-memory cache for parsed tournaments"""
import time

class TournamentCache:
    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        self._cache = {}

    def get(self, guild_id: int):
        if guild_id in self._cache:
            entry = self._cache[guild_id]
            if time.time() - entry["ts"] < self.ttl:
                return entry["data"]
        return None

    def set(self, guild_id: int, data: list):
        self._cache[guild_id] = {"ts": time.time(), "data": data}
