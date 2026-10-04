import time
from collections import defaultdict

class LevelingManager:
    def __init__(self, db):
        self.db = db
        self.last_xp_time = defaultdict(float)

    def process_message(self, guild_id: int, user_id: int, rate: float = 1.0) -> tuple[int, int, bool]:
        """
        Attribue de l'XP si le cooldown de 60s est respecté.
        Renvoie (xp, niveau, level_up_boolean).
        """
        now = time.time()
        last = self.last_xp_time[(guild_id, user_id)]
        if now - last < 60:
            user_data = self.db.get_user_level(guild_id, user_id)
            return user_data["xp"], user_data["level"], False

        self.last_xp_time[(guild_id, user_id)] = now
        gain = int(15 * max(0.1, rate))
        return self.db.add_xp(guild_id, user_id, amount=gain)

    def get_rank_info(self, guild_id: int, user_id: int) -> dict:
        user_level = self.db.get_user_level(guild_id, user_id)
        xp = user_level["xp"]
        level = user_level["level"]
        # XP requis pour le prochain niveau
        next_level_xp = ((level + 1) ** 2) * 100
        current_level_base = (level ** 2) * 100
        progress = xp - current_level_base
        needed = next_level_xp - current_level_base

        leaderboard = self.db.get_leaderboard(guild_id, limit=100)
        rank = 1
        for idx, row in enumerate(leaderboard, start=1):
            if row["user_id"] == user_id:
                rank = idx
                break

        return {
            "user_id": user_id,
            "level": level,
            "xp": xp,
            "next_level_xp": next_level_xp,
            "progress": max(0, progress),
            "needed": max(1, needed),
            "rank": rank,
            "messages": user_level.get("messages_count", 0),
        }
