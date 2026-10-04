import re


class KnowledgeManager:
    def __init__(self, db):
        self.db = db

    def learn(self, text, source, guild_id):
        cleaned = (text or "").strip()
        if not cleaned:
            return "Je n'ai rien à enregistrer."

        topic = self._extract_topic(cleaned) or "staff"
        self.db.execute(
            "INSERT INTO knowledge(guild_id, topic, content, source) VALUES (?, ?, ?, ?)",
            (guild_id, topic, cleaned, source),
        )

        fields = self._extract_tournament_fields(cleaned)
        if fields:
            self._upsert_tournament_record(guild_id, topic, fields)

        return f"Compris 😎 J'ai enregistré cette information pour **{topic}**."

    def _extract_topic(self, text):
        lowered = text.lower()
        for alias, canonical in {
            "mk squid game": "mk squid game",
            "squid game": "mk squid game",
            "mk world cup": "mk world cup",
            "world cup": "mk world cup",
            "mk champion league": "mk champion league",
            "champion league": "mk champion league",
            "squid": "mk squid game",
        }.items():
            if alias in lowered:
                return canonical.upper()

        match = re.search(r"(?:tournoi|tournament)\s+([a-z0-9à-ÿ _'-]+)", text, re.IGNORECASE)
        if match:
            topic = match.group(1).strip(" .,:;")
            if topic:
                return topic.strip().title()
        return None

    def _extract_tournament_fields(self, text):
        details = {}

        teams_match = re.search(r"(?:(\d+)\s*(?:équipes?|equipes?|teams?)|(?:équipes?|equipes?|teams?)\s*(?:actuellement\s*)?(?:sont|est|=|:|compte)?\s*(\d+))", text, re.IGNORECASE)
        if teams_match:
            details["teams"] = teams_match.group(1) or teams_match.group(2)
        if teams_match:
            details["teams"] = teams_match.group(1)

        prize_match = re.search(r"(?:prizepool|prize pool|prize|récompense|recompense|gain)\s*(?:est|:|=|-)?\s*([^\n.]+)", text, re.IGNORECASE)
        if prize_match:
            details["prizepool"] = prize_match.group(1).strip()

        rules_match = re.search(r"(?:regles|règles|règlement|reglement)\s*(?:sont|est|:|=|-)?\s*([^\n.]+)", text, re.IGNORECASE)
        if rules_match:
            details["rules"] = rules_match.group(1).strip()

        date_match = re.search(r"(?:date|jour|commence|debut|début)\s*(?:est|:|=|-)?\s*([^\n.]+)", text, re.IGNORECASE)
        if date_match:
            details["date"] = date_match.group(1).strip()

        format_match = re.search(r"(?:format)\s*(?:est|:|=|-)?\s*([^\n.]+)", text, re.IGNORECASE)
        if format_match:
            details["format"] = format_match.group(1).strip()

        status_match = re.search(r"(?:statut|status)\s*(?:est|:|=|-)?\s*([^\n.]+)", text, re.IGNORECASE)
        if status_match:
            details["status"] = status_match.group(1).strip()

        return details

    def _upsert_tournament_record(self, guild_id, name, details):
        existing = self.db.query(
            "SELECT * FROM tournaments WHERE guild_id=? AND name=? ORDER BY updated_at DESC LIMIT 1",
            (guild_id, name),
        )
        if existing:
            row = dict(existing[0])
            updates = []
            values = []
            for field in ["date", "teams", "prizepool", "format", "status", "rules"]:
                if field in details and details[field] is not None:
                    updates.append(f"{field} = ?")
                    values.append(details[field])
            if updates:
                values.extend([guild_id, name, row["id"]])
                self.db.execute(
                    f"UPDATE tournaments SET {', '.join(updates)}, updated_at=CURRENT_TIMESTAMP WHERE guild_id=? AND name=? AND id=?",
                    values,
                )
            return

        self.db.execute(
            "INSERT INTO tournaments(guild_id, channel_id, name, date, teams, prizepool, format, status, rules) VALUES (?, 0, ?, ?, ?, ?, ?, ?, ?)",
            (
                guild_id,
                name,
                details.get("date"),
                details.get("teams"),
                details.get("prizepool"),
                details.get("format"),
                details.get("status"),
                details.get("rules"),
            ),
        )

    def search_tournaments(self, query, guild_id):
        rows = self.db.query(
            "SELECT * FROM tournaments WHERE guild_id=? ORDER BY updated_at DESC",
            (guild_id,),
        )
        q = re.sub(r"\s+", " ", (query or "").lower().strip())
        if not q:
            return []

        scored = []
        for row in rows:
            item = dict(row)
            name = (item.get("name") or "").lower()
            score = 0
            if q in name:
                score += 150
            for token in re.findall(r"[a-z0-9à-ÿ]+", name):
                if len(token) >= 3 and token in q:
                    score += 12
            for field in ["rules", "format", "status", "date", "prizepool", "teams"]:
                value = item.get(field) or ""
                tokens = re.findall(r"[a-z0-9à-ÿ]+", value.lower())
                if any(token in q for token in tokens):
                    score += 6
            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        if not scored:
            for keyword in ["tournoi", "regle", "reglement", "equipes", "prize", "participer", "format"]:
                if keyword in q:
                    return [dict(r) for r in rows[:5]]
        return [item for _, item in scored[:5]]

    def get_tournament_details(self, tournament_id):
        rows = self.db.query("SELECT * FROM tournaments WHERE id=?", (tournament_id,))
        return dict(rows[0]) if rows else {}
