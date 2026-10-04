"""Guild / Server settings and channel memory"""
class ServerMemory:
    def __init__(self, db):
        self.db = db

    def get_rules(self, guild_id: int) -> str:
        return "Règles générales du serveur MK ARENA"

    def get_tournament_channel(self, guild_id: int) -> str:
        return "tournois"
