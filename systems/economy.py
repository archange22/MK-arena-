import time
import random

class EconomySystem:
    def __init__(self, db):
        self.db = db

    def get_account(self, guild_id: int, user_id: int) -> dict:
        rows = self.db.query("SELECT wallet, bank, last_daily, last_weekly, last_work FROM economy WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        if rows:
            return dict(rows[0])
        self.db.execute(
            "INSERT OR IGNORE INTO economy (guild_id, user_id, wallet, bank, last_daily, last_weekly, last_work) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (guild_id, user_id, 100, 0, 0, 0, 0)
        )
        return {"wallet": 100, "bank": 0, "last_daily": 0, "last_weekly": 0, "last_work": 0}

    def claim_daily(self, guild_id: int, user_id: int, amount: int = 250) -> tuple[bool, str, int]:
        acc = self.get_account(guild_id, user_id)
        now = int(time.time())
        cooldown = 86400 # 24h
        if now - acc["last_daily"] < cooldown:
            remaining = cooldown - (now - acc["last_daily"])
            hours = remaining // 3600
            mins = (remaining % 3600) // 60
            return False, f"Patience ! Revenez dans {hours}h {mins}m pour votre récompense quotidienne.", 0
        
        self.db.execute("UPDATE economy SET wallet = wallet + ?, last_daily = ? WHERE guild_id = ? AND user_id = ?", (amount, now, guild_id, user_id))
        return True, f"Vous avez récupéré votre récompense journalière de {amount} crédits Aperture !", amount

    def claim_weekly(self, guild_id: int, user_id: int, amount: int = 1500) -> tuple[bool, str, int]:
        acc = self.get_account(guild_id, user_id)
        now = int(time.time())
        cooldown = 604800 # 7 jours
        if now - acc["last_weekly"] < cooldown:
            remaining = cooldown - (now - acc["last_weekly"])
            days = remaining // 86400
            hours = (remaining % 86400) // 3600
            return False, f"Revenez dans {days}j {hours}h pour votre récompense hebdomadaire.", 0
        
        self.db.execute("UPDATE economy SET wallet = wallet + ?, last_weekly = ? WHERE guild_id = ? AND user_id = ?", (amount, now, guild_id, user_id))
        return True, f"Récompense hebdomadaire réclamée : +{amount} crédits !", amount

    def work(self, guild_id: int, user_id: int) -> tuple[bool, str, int]:
        acc = self.get_account(guild_id, user_id)
        now = int(time.time())
        cooldown = 3600 # 1h
        if now - acc["last_work"] < cooldown:
            mins = (cooldown - (now - acc["last_work"])) // 60
            return False, f"Reposez-vous encore {mins} minute(s) avant de retravailler.", 0
        
        earned = random.randint(80, 220)
        jobs = [
            "Calibration des tourelles MK Arena",
            "Entraînement scrim CODM Hardpoint",
            "Analyse tactique Search & Destroy",
            "Maintenance des sas de test Aperture",
            "Coaching de visée pour les recrues"
        ]
        job = random.choice(jobs)
        self.db.execute("UPDATE economy SET wallet = wallet + ?, last_work = ? WHERE guild_id = ? AND user_id = ?", (earned, now, guild_id, user_id))
        return True, f"{job} terminé avec succès ! Gain : **+{earned} crédits**.", earned

    def transfer(self, guild_id: int, from_user: int, to_user: int, amount: int) -> tuple[bool, str]:
        if amount <= 0:
            return False, "Montant invalide."
        from_acc = self.get_account(guild_id, from_user)
        if from_acc["wallet"] < amount:
            return False, "Solde insuffisant dans votre portefeuille."
        self.get_account(guild_id, to_user)
        self.db.execute("UPDATE economy SET wallet = wallet - ? WHERE guild_id = ? AND user_id = ?", (amount, guild_id, from_user))
        self.db.execute("UPDATE economy SET wallet = wallet + ? WHERE guild_id = ? AND user_id = ?", (amount, guild_id, to_user))
        return True, f"Virement de **{amount} crédits** effectué avec succès."

    def get_leaderboard(self, guild_id: int, limit: int = 10) -> list[dict]:
        rows = self.db.query(
            "SELECT user_id, (wallet + bank) as total, wallet, bank FROM economy WHERE guild_id = ? ORDER BY total DESC LIMIT ?",
            (guild_id, limit)
        )
        return [dict(r) for r in rows]
