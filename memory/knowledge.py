import re

class KnowledgeManager:
    def __init__(self, db):
        self.db = db

    def learn(self, text, source, guild_id):
        # v0.1: stocke l'énoncé comme connaissance explicite.
        topic = "staff"
        m = re.search(r"(?:tournoi|tournament)\s+([A-Za-z0-9À-ÿ _'’-]+)", text, re.IGNORECASE)
        if m:
            topic = m.group(1).strip(" .,:;")
        self.db.execute(
            "INSERT INTO knowledge(guild_id, topic, content, source) VALUES (?, ?, ?, ?)",
            (guild_id, topic, text, source),
        )
        return f"Compris 😎 J'ai enregistré cette information dans ma mémoire : **{topic}**."

    def search_tournaments(self, query, guild_id):
        rows = self.db.query(
            "SELECT * FROM tournaments WHERE guild_id=? ORDER BY updated_at DESC",
            (guild_id,),
        )
        q = query.lower()
        scored = []
        for r in rows:
            score = 0
            name = r["name"].lower()
            if name in q:
                score += 100
            for token in re.findall(r"[\wÀ-ÿ]+", name):
                if len(token) >= 3 and token in q:
                    score += 10
            for field in ("rules", "format", "status"):
                if r[field] and any(w in q for w in re.findall(r"[\wÀ-ÿ]+", r[field].lower())):
                    score += 1
            if score > 0:
                scored.append((score, dict(r)))
        scored.sort(key=lambda x: x[0], reverse=True)
        if not scored:
            # Pour une demande générique de tournoi, retourner les plus récents.
            if any(w in q for w in ["tournoi", "règle", "regle", "règlement", "reglement", "prize", "équipe", "equipe", "particip"]):
                return [dict(r) for r in rows[:5]]
        return [r for _, r in scored[:5]]

    def get_tournament_details(self, tournament_id):
        rows = self.db.query("SELECT * FROM tournaments WHERE id=?", (tournament_id,))
        return dict(rows[0]) if rows else {}
