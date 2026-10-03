import re
from discord import TextChannel

class TournamentScanner:
    def __init__(self, client, db, category_id):
        self.client = client
        self.db = db
        self.category_id = category_id

    async def sync(self):
        if not self.category_id:
            return 0
        count = 0
        for guild in self.client.guilds:
            category = guild.get_channel(self.category_id)
            if not category:
                continue
            for channel in category.channels:
                if not isinstance(channel, TextChannel):
                    continue
                count += 1
                await self._scan_channel(guild.id, channel)
        return count

    async def _scan_channel(self, guild_id, channel):
        messages = []
        async for message in channel.history(limit=200, oldest_first=False):
            if not message.author.bot:
                messages.append(message)
        if not messages:
            self.db.execute(
                """INSERT INTO tournaments(guild_id, channel_id, name)
                   VALUES (?, ?, ?)
                   ON CONFLICT(channel_id) DO UPDATE SET name=excluded.name, updated_at=CURRENT_TIMESTAMP""",
                (guild_id, channel.id, channel.name.replace("-", " ").replace("_", " ").title()),
            )
            return

        combined = "\n".join(m.content for m in reversed(messages) if m.content)
        name = channel.name.replace("-", " ").replace("_", " ").title()
        parsed = self._parse(combined)
        self.db.execute(
            """INSERT INTO tournaments
               (guild_id, channel_id, name, date, teams, prizepool, format, status, rules, source_message_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(channel_id) DO UPDATE SET
                 name=excluded.name, date=excluded.date, teams=excluded.teams,
                 prizepool=excluded.prizepool, format=excluded.format,
                 status=excluded.status, rules=excluded.rules,
                 source_message_id=excluded.source_message_id,
                 updated_at=CURRENT_TIMESTAMP""",
            (
                guild_id, channel.id, name, parsed["date"], parsed["teams"],
                parsed["prizepool"], parsed["format"], parsed["status"],
                parsed["rules"], messages[0].id
            )
        )
        for m in messages:
            if m.content:
                self.db.execute(
                    """INSERT INTO tournament_messages(message_id, channel_id, content)
                       VALUES (?, ?, ?)
                       ON CONFLICT(message_id) DO UPDATE SET content=excluded.content, updated_at=CURRENT_TIMESTAMP""",
                    (m.id, channel.id, m.content)
                )

    def _parse(self, text):
        def find(patterns):
            for p in patterns:
                m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
                if m:
                    return m.group(1).strip()
            return None

        date = find([r"(?:date|jour)\s*[:=-]\s*(.+)", r"(\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})"])
        teams = find([r"(?:équipes|equipes|teams)\s*[:=-]\s*(\d+)"])
        prize = find([r"(?:prizepool|prize|récompense|recompense)\s*[:=-]\s*([^\n]+)"])
        fmt = find([r"(?:format)\s*[:=-]\s*([^\n]+)", r"\b(BO[1-9])\b"])
        status = find([r"(?:statut|status)\s*[:=-]\s*([^\n]+)"])
        rules = find([r"(?:règles|regles|règlement|reglement)\s*[:=-]\s*(.+?)(?=\n\s*\w+\s*[:=-]|$)"])
        return {"date": date, "teams": teams, "prizepool": prize, "format": fmt, "status": status, "rules": rules}
