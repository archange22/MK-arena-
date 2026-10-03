from datetime import datetime, timezone


class ConversationContext:
    def __init__(self, ttl_minutes: int = 30):
        self.ttl_minutes = ttl_minutes

    def normalize(self, text: str) -> str:
        return " ".join(str(text or "").lower().strip().split())

    def is_follow_up(self, text: str) -> bool:
        normalized = self.normalize(text)
        return bool(normalized.startswith(("et ", "alors ", "et le ", "et sa ", "et les ", "puis ")))


class ConversationMemory:
    def __init__(self, db, ttl_minutes=30, max_messages=20):
        self.db = db
        self.ttl_minutes = ttl_minutes
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
        return list(reversed([dict(row) for row in rows]))

    def recent_valid(self, user_id, limit=None):
        rows = self.recent(user_id, limit=limit)
        cutoff = datetime.now(timezone.utc).timestamp() - (self.ttl_minutes * 60)
        valid = []
        for row in rows:
            try:
                created = row.get("created_at")
                if not created:
                    continue
                dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
                if dt.timestamp() >= cutoff:
                    valid.append(row)
            except ValueError:
                continue
        return valid

    def latest_tournament_hint(self, user_id):
        rows = self.recent_valid(user_id, limit=self.max_messages)
        for row in reversed(rows):
            content = str(row.get("content") or "").lower()
            for name in [
                "mk squid game",
                "squid game",
                "mk world cup",
                "world cup",
                "mk champion league",
                "champion league",
            ]:
                if name in content:
                    return name.title()
        return None

    def build_context_summary(self, user_id):
        rows = self.recent_valid(user_id, limit=self.max_messages)
        if not rows:
            return ""
        return " ".join(f"{row['role']}: {row['content']}" for row in rows)
