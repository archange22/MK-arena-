from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, List
try:
    import discord
except ImportError:
    discord = None


class AntiRaidManager:
    def __init__(self, max_joins: int = 5, window_seconds: int = 10):
        self.max_joins = max_joins
        self.window_seconds = window_seconds
        self.join_history: Dict[int, List[float]] = defaultdict(list)
        self.lockdown_active: Dict[int, bool] = defaultdict(bool)
        self.enabled: Dict[int, bool] = defaultdict(lambda: True)

    def is_enabled(self, guild_id: int) -> bool:
        return self.enabled[guild_id]

    def set_enabled(self, guild_id: int, state: bool):
        self.enabled[guild_id] = state

    def record_join(self, guild_id: int, timestamp: float | None = None) -> bool:
        if not self.enabled[guild_id]:
            return False

        now = timestamp or time.time()
        cutoff = now - self.window_seconds
        
        # Nettoie les anciens joins
        self.join_history[guild_id] = [t for t in self.join_history[guild_id] if t >= cutoff]
        self.join_history[guild_id].append(now)

        if len(self.join_history[guild_id]) >= self.max_joins:
            self.lockdown_active[guild_id] = True
            return True
        return False

    def is_in_lockdown(self, guild_id: int) -> bool:
        return self.lockdown_active[guild_id]

    def set_lockdown(self, guild_id: int, active: bool):
        self.lockdown_active[guild_id] = active

    async def apply_guild_lockdown(self, guild: discord.Guild, lock: bool = True) -> int:
        count = 0
        self.lockdown_active[guild.id] = lock
        default_role = guild.default_role

        for channel in guild.text_channels:
            try:
                overwrites = channel.overwrites_for(default_role)
                if lock:
                    overwrites.send_messages = False
                else:
                    overwrites.send_messages = None
                await channel.set_permissions(default_role, overwrite=overwrites)
                count += 1
            except Exception:
                continue
        return count
