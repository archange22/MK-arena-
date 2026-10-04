"""Per-user memory and preferences"""
class UserMemory:
    def __init__(self, db):
        self.db = db

    def get_preferences(self, user_id: int) -> dict:
        return {"user_id": user_id, "language": "fr", "tone": "friendly"}

    def get_history_summary(self, user_id: int) -> str:
        return f"Historique pour utilisateur {user_id}"
