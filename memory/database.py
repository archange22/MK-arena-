import sqlite3
from threading import RLock


class Database:
    def __init__(self, path):
        self.path = path
        self.lock = RLock()
        self._shared_conn = None
        if path == ":memory:":
            self._shared_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._shared_conn.row_factory = sqlite3.Row

    def connect(self):
        if self._shared_conn is not None:
            return self._shared_conn
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self):
        with self.lock:
            conn = self.connect()
            conn.executescript(
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

                CREATE INDEX IF NOT EXISTS idx_knowledge_guild ON knowledge(guild_id);
                CREATE INDEX IF NOT EXISTS idx_tournaments_guild ON tournaments(guild_id);
                CREATE INDEX IF NOT EXISTS idx_tournaments_name ON tournaments(name);
                """
            )
            conn.commit()

    def execute(self, sql, params=()):
        with self.lock:
            conn = self.connect()
            cur = conn.execute(sql, params)
            conn.commit()
            return cur.lastrowid

    def query(self, sql, params=()):
        with self.lock:
            conn = self.connect()
            return conn.execute(sql, params).fetchall()

    def count_tournaments(self):
        row = self.query("SELECT COUNT(*) AS n FROM tournaments")[0]
        return row["n"]

    def count_knowledge(self):
        row = self.query("SELECT COUNT(*) AS n FROM knowledge")[0]
        return row["n"]
