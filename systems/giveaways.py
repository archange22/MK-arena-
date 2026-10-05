import time
import random
import json

class GiveawaySystem:
    def __init__(self, db):
        self.db = db

    def start_giveaway(self, guild_id: int, channel_id: int, prize: str, winners: int, duration_sec: int) -> int:
        end_time = int(time.time()) + duration_sec
        cur = self.db.execute(
            """INSERT INTO giveaways (guild_id, channel_id, prize, winners_count, end_time, status, entries_json)
               VALUES (?, ?, ?, ?, ?, 'active', '[]')""",
            (guild_id, channel_id, prize, winners, end_time)
        )
        return cur

    def enter_giveaway(self, giveaway_id: int, user_id: int) -> tuple[bool, str]:
        rows = self.db.query("SELECT * FROM giveaways WHERE id = ? AND status = 'active'", (giveaway_id,))
        if not rows:
            return False, "Ce giveaway n'est plus actif."
        g = dict(rows[0])
        entries = json.loads(g["entries_json"] or "[]")
        if user_id in entries:
            return False, "Vous participez déjà à ce tirage au sort."
        entries.append(user_id)
        self.db.execute("UPDATE giveaways SET entries_json = ? WHERE id = ?", (json.dumps(entries), giveaway_id))
        return True, f"Participation enregistrée ! Total participants : {len(entries)}."

    def draw_winners(self, giveaway_id: int) -> tuple[bool, list[int], str]:
        rows = self.db.query("SELECT * FROM giveaways WHERE id = ?", (giveaway_id,))
        if not rows:
            return False, [], "Giveaway introuvable."
        g = dict(rows[0])
        entries = json.loads(g["entries_json"] or "[]")
        if not entries:
            self.db.execute("UPDATE giveaways SET status = 'ended' WHERE id = ?", (giveaway_id,))
            return False, [], "Aucun participant au tirage."
        
        count = min(g["winners_count"], len(entries))
        winners = random.sample(entries, count)
        self.db.execute("UPDATE giveaways SET status = 'ended' WHERE id = ?", (giveaway_id,))
        return True, winners, g["prize"]
