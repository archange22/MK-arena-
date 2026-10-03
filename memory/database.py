import sqlite3
from threading import RLock


class Database:
    def __init__(self, path):
        self.path = path
        self.lock = RLock()

    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self):
        with self.lock, self.connect() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    topic TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS tournaments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL DEFAULT 0,
                    name TEXT NOT NULL,
                    date TEXT,
                    teams TEXT,
                    prizepool TEXT,
                    format TEXT,
                    status TEXT,
                    rules TEXT,
                    source_message_id INTEGER,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS tournament_messages (
                    message_id INTEGER PRIMARY KEY,
                    channel_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS tournament_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    tournament_id INTEGER NOT NULL,
                    field TEXT NOT NULL,
                    value TEXT,
                    UNIQUE(guild_id, tournament_id, field)
                );
                CREATE INDEX IF NOT EXISTS idx_knowledge_guild ON knowledge(guild_id);
                CREATE INDEX IF NOT EXISTS idx_tournaments_guild ON tournaments(guild_id);
                CREATE INDEX IF NOT EXISTS idx_tournaments_name ON tournaments(name);
                CREATE INDEX IF NOT EXISTS idx_tournament_data ON tournament_data(guild_id, tournament_id, field);
                """
            )

    def execute(self, sql, params=()):
        with self.lock, self.connect() as c:
            cur = c.execute(sql, params)
            return cur.lastrowid

    def query(self, sql, params=()):
        with self.lock, self.connect() as c:
            return c.execute(sql, params).fetchall()

    def count_tournaments(self):
        row = self.query("SELECT COUNT(*) AS n FROM tournaments")[0]
        return row["n"]

    def count_knowledge(self):
        row = self.query("SELECT COUNT(*) AS n FROM knowledge")[0]
        return row["n"]
