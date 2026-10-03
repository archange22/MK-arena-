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

        details = self._extract_tournament_fields(cleaned)
        if details and topic:
            self._upsert_tournament(guild_id, topic, details)

        return f"Compris 😎 J'ai enregistré cette information pour **{topic}**."

    def _extract_topic(self, text):
        match = re.search(r"(?:tournoi|tournament|mk\s+[a-z0-9à-ÿ _'-]+)", text, re.IGNORECASE)
        if match:
            topic = match.group(0).strip().replace("tournoi ", "").replace("tournament ", "")
            topic = re.sub(r"\s+", " ", topic).strip()
            if topic:
                return topic.title()
        if "squid" in text.lower():
            return "MK SQUID GAME"
        return None

    def _extract_tournament_fields(self, text):
        details = {}
        if re.search(r"(equipes|teams?)", text, re.IGNORECASE):
            match = re.search(r"(?:equipes|teams?)\s*(?:actuellement\s*)?(?:sont|sont\s*\=?\s*|est|\=)?\s*(\d+)", text, re.IGNORECASE)
            if match:
                details["teams"] = match.group(1)

        prize_match = re.search(r"(?:prizepool|prize\s*pool|prix|récompense|recompense)\s*(?:est|:|=|-)?\s*([^\n\.]+)", text, re.IGNORECASE)
        if prize_match:
            details["prizepool"] = prize_match.group(1).strip()

        rules_match = re.search(r"(?:règles|regles|règlement|reglement)\s*(?:est|:|=|-)?\s*([^\n\.]+)", text, re.IGNORECASE)
        if rules_match:
            details["rules"] = rules_match.group(1).strip()

        date_match = re.search(r"(?:date|jour|commence|debut|début)\s*(?:est|:|=|-)?\s*([^\n\.]+)", text, re.IGNORECASE)
        if date_match:
            details["date"] = date_match.group(1).strip()

        format_match = re.search(r"(?:format)\s*(?:est|:|=|-)?\s*([^\n\.]+)", text, re.IGNORECASE)
        if format_match:
            details["format"] = format_match.group(1).strip()

        status_match = re.search(r"(?:statut|status)\s*(?:est|:|=|-)?\s*([^\n\.]+)", text, re.IGNORECASE)
        if status_match:
            details["status"] = status_match.group(1).strip()

        return details

    def _upsert_tournament(self, guild_id, name, details):
        existing = self.db.query(
            "SELECT * FROM tournaments WHERE guild_id=? AND name=? ORDER BY updated_at DESC LIMIT 1",
            (guild_id, name),
        )
        if existing:
            row = dict(existing[0])
            update_fields = []
            values = []
            for key in ["date", "teams", "prizepool", "format", "status", "rules"]:
                if key in details and details[key] is not None:
                    update_fields.append(f"{key} = ?")
                    values.append(details[key])
            if update_fields:
                values.extend([name, guild_id, row["id"]])
                self.db.execute(
                    f"UPDATE tournaments SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE guild_id=? AND name=? AND id=?",
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
        for r in rows:
            row = dict(r)
            name = (row.get("name") or "").lower()
            score = 0
            if q in name:
                score += 100
            for token in re.findall(r"[a-z0-9à-ÿ]+", name):
                if len(token) >= 3 and token in q:
                    score += 10
            for field in ["rules", "format", "status", "date", "prizepool", "teams"]:
                value = row.get(field) or ""
                if value:
                    field_tokens = re.findall(r"[a-z0-9à-ÿ]+", value.lower())
                    if any(token in q for token in field_tokens):
                        score += 3
            if score > 0:
                scored.append((score, row))

        scored.sort(key=lambda x: x[0], reverse=True)
        if not scored:
            for w in ["tournoi", "regle", "reglement", "equipes", "prize", "participer", "format"]:
                if w in q:
                    return [dict(r) for r in rows[:5]]
        return [row for _, row in scored[:5]]

    def get_tournament_details(self, tournament_id):
        rows = self.db.query("SELECT * FROM tournaments WHERE id=?", (tournament_id,))
        return dict(rows[0]) if rows else {}
