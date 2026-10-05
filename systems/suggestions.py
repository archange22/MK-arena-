class SuggestionSystem:
    def __init__(self, db):
        self.db = db

    def add_suggestion(self, guild_id: int, user_id: int, content: str) -> int:
        cur = self.db.execute(
            """INSERT INTO suggestions (guild_id, user_id, content, status, upvotes, downvotes)
               VALUES (?, ?, ?, 'pending', 0, 0)""",
            (guild_id, user_id, content)
        )
        return cur

    def vote_suggestion(self, suggestion_id: int, user_id: int, up: bool) -> tuple[bool, int, int]:
        rows = self.db.query("SELECT upvotes, downvotes FROM suggestions WHERE id = ?", (suggestion_id,))
        if not rows:
            return False, 0, 0
        if up:
            self.db.execute("UPDATE suggestions SET upvotes = upvotes + 1 WHERE id = ?", (suggestion_id,))
        else:
            self.db.execute("UPDATE suggestions SET downvotes = downvotes + 1 WHERE id = ?", (suggestion_id,))
        r = self.db.query("SELECT upvotes, downvotes FROM suggestions WHERE id = ?", (suggestion_id,))[0]
        return True, r["upvotes"], r["downvotes"]

    def set_status(self, suggestion_id: int, status: str) -> bool:
        self.db.execute("UPDATE suggestions SET status = ? WHERE id = ?", (status, suggestion_id))
        return True
