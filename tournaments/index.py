import logging
from tournaments.parser import extract_tournament_fields

logger = logging.getLogger(__name__)


class TournamentIndexer:
    def __init__(self, db):
        self.db = db

    def index_message(self, guild_id: int, channel_id: int, message_id: int, content: str):
        if not content:
            return

        # Enregistre le message brut pour historique
        self.db.execute(
            "INSERT OR REPLACE INTO tournament_messages(message_id, channel_id, content) VALUES (?, ?, ?)",
            (message_id, channel_id, content),
        )

        # Extraction des données structurées
        fields = extract_tournament_fields(content)
        if fields:
            name = fields.get("name") or "MK SQUID GAME"
            # Vérifier si existe déjà
            existing = self.db.query(
                "SELECT * FROM tournaments WHERE guild_id = ? AND name = ?",
                (guild_id, name),
            )
            if existing:
                self.db.execute(
                    """
                    UPDATE tournaments
                    SET date = COALESCE(?, date),
                        teams = COALESCE(?, teams),
                        prizepool = COALESCE(?, prizepool),
                        format = COALESCE(?, format),
                        rules = COALESCE(?, rules),
                        source_message_id = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE guild_id = ? AND name = ?
                    """,
                    (
                        fields.get("date"),
                        fields.get("teams"),
                        fields.get("prizepool"),
                        fields.get("format"),
                        fields.get("rules"),
                        message_id,
                        guild_id,
                        name,
                    ),
                )
            else:
                self.db.execute(
                    """
                    INSERT INTO tournaments(guild_id, channel_id, name, date, teams, prizepool, format, rules, source_message_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        guild_id,
                        channel_id,
                        name,
                        fields.get("date"),
                        fields.get("teams"),
                        fields.get("prizepool"),
                        fields.get("format"),
                        fields.get("rules"),
                        message_id,
                    ),
                )
