from __future__ import annotations

from datetime import datetime, timedelta, timezone


class ConversationMemory:
    def __init__(self, db, ttl_minutes=30, max_messages=20):
        self.db = db
        self.ttl = timedelta(minutes=ttl_minutes)
        self.max_messages = max_messages

    def add(self, user_id, role, content):
        self.db.execute(
            "INSERT INTO conversations(user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )

    def recent(self, user_id, limit=None):
        limit = limit or self.max_messages
        rows = self.db.query(
            "SELECT role, content, created_at FROM conversations WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        normalized = []
        for row in rows:
            normalized.append(dict(row))
        return list(reversed(normalized))

    def recent_valid(self, user_id, limit=None):
        rows = self.recent(user_id, limit=limit)
        cutoff = datetime.now(timezone.utc) - self.ttl
        valid = []
        for row in rows:
            created = row.get("created_at")
            if not created:
                continue
            try:
                dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
            except ValueError:
                continue
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if dt >= cutoff:
                valid.append(row)
        return valid

    def build_summary(self, user_id):
        rows = self.recent_valid(user_id, limit=self.max_messages)
        if not rows:
            return ""
        return " ".join(f"{row['role']}: {row['content']}" for row in rows)

    def latest_tournament_hint(self, user_id):
        rows = self.recent_valid(user_id, limit=self.max_messages)
        for row in reversed(rows):
            text = (row.get("content") or "").lower()
            for alias, canonical in {
                "mk squid game": "mk squid game",
                "squid game": "mk squid game",
                "mk world cup": "mk world cup",
                "world cup": "mk world cup",
                "mk champion league": "mk champion league",
                "champion league": "mk champion league",
                "squid": "mk squid game",
            }.items():
                if alias in text:
                    return canonical
        return None
