from datetime import datetime, timedelta, timezone

class ConversationMemory:
    def __init__(self, db, ttl_minutes=30):
        self.db = db
        self.ttl = timedelta(minutes=ttl_minutes)

    def add(self, user_id, role, content):
        self.db.execute(
            "INSERT INTO conversations(user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )

    def recent(self, user_id, limit=10):
        rows = self.db.query(
            "SELECT role, content, created_at FROM conversations WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        return list(reversed(rows))
