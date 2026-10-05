import sqlite3
import json
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
        conn = sqlite3.connect(self.path, check_same_thread=False)
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

                -- Table pour les réglages par serveur (Panel Admin style DraftBot)
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    welcome_enabled INTEGER DEFAULT 0,
                    welcome_channel_id INTEGER,
                    welcome_message TEXT DEFAULT "Bienvenue {user} sur {server} ! Tu es le {count}ème membre.",
                    leave_enabled INTEGER DEFAULT 0,
                    leave_channel_id INTEGER,
                    leave_message TEXT DEFAULT "Au revoir {user}...",
                    autorole_id INTEGER,
                    automod_links INTEGER DEFAULT 0,
                    automod_invites INTEGER DEFAULT 0,
                    automod_spam INTEGER DEFAULT 0,
                    automod_caps INTEGER DEFAULT 0,
                    automod_blacklist TEXT DEFAULT "",
                    logs_channel_id INTEGER,
                    ticket_category_id INTEGER,
                    ticket_support_role_id INTEGER,
                    ticket_transcript_channel_id INTEGER,
                    xp_enabled INTEGER DEFAULT 1,
                    xp_rate REAL DEFAULT 1.0,
                    glados_core TEXT DEFAULT "curiosity",
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                -- Table des avertissements (Warns)
                CREATE TABLE IF NOT EXISTS warns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                -- Table des niveaux et XP
                CREATE TABLE IF NOT EXISTS user_levels (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 0,
                    messages_count INTEGER DEFAULT 0,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, user_id)
                );

                -- Table des rôles par réaction
                CREATE TABLE IF NOT EXISTS reaction_roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    emoji TEXT NOT NULL,
                    label TEXT
                );

                -- Table des déclencheurs et commandes personnalisées (Custom Triggers)
                CREATE TABLE IF NOT EXISTS custom_triggers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    trigger_text TEXT NOT NULL,
                    response_text TEXT NOT NULL,
                    action_type TEXT DEFAULT "reply",
                    created_by INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                -- Table de rancune et d'humeur envers les utilisateurs (Grudge Level)
                CREATE TABLE IF NOT EXISTS user_grudges (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    grudge_level INTEGER DEFAULT 0,
                    last_insult TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, user_id)
                );

                CREATE INDEX IF NOT EXISTS idx_knowledge_guild ON knowledge(guild_id);
                CREATE INDEX IF NOT EXISTS idx_tournaments_guild ON tournaments(guild_id);
                CREATE INDEX IF NOT EXISTS idx_tournaments_name ON tournaments(name);
                CREATE INDEX IF NOT EXISTS idx_warns_guild_user ON warns(guild_id, user_id);
                CREATE INDEX IF NOT EXISTS idx_levels_guild_xp ON user_levels(guild_id, xp DESC);
                CREATE INDEX IF NOT EXISTS idx_triggers_guild ON custom_triggers(guild_id);
                CREATE INDEX IF NOT EXISTS idx_triggers_text ON custom_triggers(guild_id, trigger_text);

                -- Table Economie (Wallet, Banque, Daily, Weekly, Work)
                CREATE TABLE IF NOT EXISTS economy (
                    guild_id INTEGER,
                    user_id INTEGER,
                    wallet INTEGER DEFAULT 100,
                    bank INTEGER DEFAULT 0,
                    last_daily INTEGER DEFAULT 0,
                    last_weekly INTEGER DEFAULT 0,
                    last_work INTEGER DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                );

                -- Table Drafts Compétitifs (Capitaines, Pool, Teams, Bans Maps/Armes)
                CREATE TABLE IF NOT EXISTS competitive_drafts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    captain1_id INTEGER,
                    captain2_id INTEGER,
                    bo_type TEXT DEFAULT 'BO3',
                    state TEXT DEFAULT 'recruiting',
                    pool_json TEXT,
                    team1_json TEXT,
                    team2_json TEXT,
                    bans_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Table Giveaways (Lots, Gagnants, Tirage)
                CREATE TABLE IF NOT EXISTS giveaways (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    channel_id INTEGER,
                    prize TEXT,
                    winners_count INTEGER DEFAULT 1,
                    end_time INTEGER,
                    status TEXT DEFAULT 'active',
                    entries_json TEXT
                );

                -- Table Sondages (Polls interactifs)
                CREATE TABLE IF NOT EXISTS polls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    question TEXT,
                    options_json TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Table Suggestions (Idées et votes communautaires)
                CREATE TABLE IF NOT EXISTS suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    content TEXT,
                    status TEXT DEFAULT 'pending',
                    upvotes INTEGER DEFAULT 0,
                    downvotes INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

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

    # --- Guild Settings (Panel Admin) ---
    def get_guild_settings(self, guild_id: int) -> dict:
        rows = self.query("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,))
        if rows:
            return dict(rows[0])
        # Default settings
        return {
            "guild_id": guild_id,
            "welcome_enabled": 0,
            "welcome_channel_id": None,
            "welcome_message": "Bienvenue {user} sur {server} ! Tu es le {count}ème sujet de test.",
            "leave_enabled": 0,
            "leave_channel_id": None,
            "leave_message": "Au revoir {user}. Ton départ a été consigné.",
            "autorole_id": None,
            "automod_links": 0,
            "automod_invites": 0,
            "automod_spam": 0,
            "automod_caps": 0,
            "automod_blacklist": "",
            "logs_channel_id": None,
            "ticket_category_id": None,
            "ticket_support_role_id": None,
            "ticket_transcript_channel_id": None,
            "xp_enabled": 1,
            "xp_rate": 1.0,
            "glados_core": "curiosity",
        }

    def save_guild_settings(self, guild_id: int, settings: dict):
        current = self.get_guild_settings(guild_id)
        current.update(settings)
        sql = """
            INSERT INTO guild_settings (
                guild_id, welcome_enabled, welcome_channel_id, welcome_message,
                leave_enabled, leave_channel_id, leave_message, autorole_id,
                automod_links, automod_invites, automod_spam, automod_caps,
                automod_blacklist, logs_channel_id, ticket_category_id,
                ticket_support_role_id, ticket_transcript_channel_id,
                xp_enabled, xp_rate, glados_core, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id) DO UPDATE SET
                welcome_enabled=excluded.welcome_enabled,
                welcome_channel_id=excluded.welcome_channel_id,
                welcome_message=excluded.welcome_message,
                leave_enabled=excluded.leave_enabled,
                leave_channel_id=excluded.leave_channel_id,
                leave_message=excluded.leave_message,
                autorole_id=excluded.autorole_id,
                automod_links=excluded.automod_links,
                automod_invites=excluded.automod_invites,
                automod_spam=excluded.automod_spam,
                automod_caps=excluded.automod_caps,
                automod_blacklist=excluded.automod_blacklist,
                logs_channel_id=excluded.logs_channel_id,
                ticket_category_id=excluded.ticket_category_id,
                ticket_support_role_id=excluded.ticket_support_role_id,
                ticket_transcript_channel_id=excluded.ticket_transcript_channel_id,
                xp_enabled=excluded.xp_enabled,
                xp_rate=excluded.xp_rate,
                glados_core=excluded.glados_core,
                updated_at=CURRENT_TIMESTAMP
        """
        self.execute(sql, (
            guild_id,
            int(current.get("welcome_enabled", 0)),
            current.get("welcome_channel_id"),
            current.get("welcome_message"),
            int(current.get("leave_enabled", 0)),
            current.get("leave_channel_id"),
            current.get("leave_message"),
            current.get("autorole_id"),
            int(current.get("automod_links", 0)),
            int(current.get("automod_invites", 0)),
            int(current.get("automod_spam", 0)),
            int(current.get("automod_caps", 0)),
            current.get("automod_blacklist", ""),
            current.get("logs_channel_id"),
            current.get("ticket_category_id"),
            current.get("ticket_support_role_id"),
            current.get("ticket_transcript_channel_id"),
            float(current.get("xp_rate", 1.0)),
            float(current.get("xp_rate", 1.0)),
            current.get("glados_core", "curiosity")
        ))

    # --- Warns System (DraftBot like) ---
    def add_warn(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
        return self.execute(
            "INSERT INTO warns (guild_id, user_id, moderator_id, reason) VALUES (?, ?, ?, ?)",
            (guild_id, user_id, moderator_id, reason),
        )

    def get_warns(self, guild_id: int, user_id: int):
        rows = self.query(
            "SELECT * FROM warns WHERE guild_id = ? AND user_id = ? ORDER BY id DESC",
            (guild_id, user_id),
        )
        return [dict(r) for r in rows]

    def remove_warn(self, warn_id: int):
        self.execute("DELETE FROM warns WHERE id = ?", (warn_id,))

    def clear_warns(self, guild_id: int, user_id: int):
        self.execute("DELETE FROM warns WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))

    def count_warns(self, guild_id: int = None):
        if guild_id:
            row = self.query("SELECT COUNT(*) as n FROM warns WHERE guild_id = ?", (guild_id,))[0]
        else:
            row = self.query("SELECT COUNT(*) as n FROM warns")[0]
        return row["n"]

    # --- Leveling / XP System ---
    def add_xp(self, guild_id: int, user_id: int, amount: int = 15) -> tuple[int, int, bool]:
        """Ajoute de l'XP et renvoie (xp_actuel, niveau, level_up)"""
        rows = self.query("SELECT xp, level, messages_count FROM user_levels WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        if rows:
            xp = rows[0]["xp"] + amount
            messages = rows[0]["messages_count"] + 1
            old_level = rows[0]["level"]
        else:
            xp = amount
            messages = 1
            old_level = 0

        new_level = int((xp / 100) ** 0.5)
        level_up = new_level > old_level

        sql = """
            INSERT INTO user_levels (guild_id, user_id, xp, level, messages_count, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET
                xp=excluded.xp,
                level=excluded.level,
                messages_count=excluded.messages_count,
                updated_at=CURRENT_TIMESTAMP
        """
        self.execute(sql, (guild_id, user_id, xp, new_level, messages))
        return xp, new_level, level_up

    def get_user_level(self, guild_id: int, user_id: int) -> dict:
        rows = self.query("SELECT * FROM user_levels WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        if rows:
            return dict(rows[0])
        return {"guild_id": guild_id, "user_id": user_id, "xp": 0, "level": 0, "messages_count": 0}

    def get_leaderboard(self, guild_id: int, limit: int = 10):
        rows = self.query(
            "SELECT * FROM user_levels WHERE guild_id = ? ORDER BY xp DESC LIMIT ?",
            (guild_id, limit),
        )
        return [dict(r) for r in rows]


    # --- Custom Triggers / Commandes personnalisées ---
    def add_custom_trigger(self, guild_id: int, trigger_text: str, response_text: str, created_by: int = None, action_type: str = "reply") -> int:
        clean_trig = trigger_text.strip().lower()
        # Delete previous matching trigger if exists
        self.execute("DELETE FROM custom_triggers WHERE guild_id = ? AND LOWER(trigger_text) = ?", (guild_id, clean_trig))
        sql = """
            INSERT INTO custom_triggers (guild_id, trigger_text, response_text, action_type, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        return self.execute(sql, (guild_id, trigger_text.strip(), response_text.strip(), action_type, created_by))

    def get_custom_triggers(self, guild_id: int) -> list[dict]:
        rows = self.query("SELECT * FROM custom_triggers WHERE guild_id = ? ORDER BY id DESC", (guild_id,))
        return [dict(r) for r in rows]

    def find_matching_trigger(self, guild_id: int, text: str) -> dict | None:
        if not text:
            return None
        cleaned = text.strip().lower()
        triggers = self.get_custom_triggers(guild_id)
        for t in triggers:
            trig_val = t["trigger_text"].strip().lower()
            if cleaned == trig_val or cleaned.startswith(trig_val + " ") or cleaned.startswith(trig_val + ":"):
                return t
        return None

    def delete_custom_trigger(self, guild_id: int, trigger_text: str) -> bool:
        clean_trig = trigger_text.strip().lower()
        rows = self.query("SELECT id FROM custom_triggers WHERE guild_id = ? AND LOWER(trigger_text) = ?", (guild_id, clean_trig))
        if rows:
            self.execute("DELETE FROM custom_triggers WHERE guild_id = ? AND LOWER(trigger_text) = ?", (guild_id, clean_trig))
            return True
        return False

    def delete_custom_trigger_by_id(self, guild_id: int, trigger_id: int) -> bool:
        rows = self.query("SELECT id FROM custom_triggers WHERE guild_id = ? AND id = ?", (guild_id, trigger_id))
        if rows:
            self.execute("DELETE FROM custom_triggers WHERE guild_id = ? AND id = ?", (guild_id, trigger_id))
            return True
        return False

    # --- Gestion de la rancune / Humeur (Grudge System) ---
    def get_user_grudge(self, guild_id: int, user_id: int) -> int:
        rows = self.query("SELECT grudge_level FROM user_grudges WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        if rows:
            return int(rows[0]["grudge_level"] or 0)
        return 0

    def increment_user_grudge(self, guild_id: int, user_id: int, reason: str = "") -> int:
        current = self.get_user_grudge(guild_id, user_id)
        new_level = min(current + 1, 5)
        sql = """
            INSERT INTO user_grudges (guild_id, user_id, grudge_level, last_insult, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET
                grudge_level = excluded.grudge_level,
                last_insult = excluded.last_insult,
                updated_at = CURRENT_TIMESTAMP
        """
        self.execute(sql, (guild_id, user_id, new_level, reason))
        return new_level

    def reset_user_grudge(self, guild_id: int, user_id: int):
        sql = """
            INSERT INTO user_grudges (guild_id, user_id, grudge_level, last_insult, updated_at)
            VALUES (?, ?, 0, '', CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET
                grudge_level = 0,
                last_insult = '',
                updated_at = CURRENT_TIMESTAMP
        """
        self.execute(sql, (guild_id, user_id))
