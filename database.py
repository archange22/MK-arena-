"""Database adapter for MK Arena: SQLite by default, PostgreSQL/Supabase when enabled."""
from __future__ import annotations
import os
import re
from typing import Any
import psycopg

DATABASE_BACKEND = os.getenv("DATABASE_BACKEND", "sqlite").strip().lower()
if DATABASE_BACKEND not in {"sqlite", "supabase"}:
    raise RuntimeError("DATABASE_BACKEND doit être 'sqlite' ou 'supabase'.")
DB_PATH = os.getenv("SQLITE_PATH", "mk_arena.db")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL", "").strip()
_TABLES = ("guild_settings", "user_xp", "warnings", "tickets")

class SupabaseConnection:
    """Small adapter preserving the bot's existing execute/fetch SQL call style."""
    def __init__(self, connection: psycopg.Connection):
        self._connection = connection
    def __enter__(self) -> "SupabaseConnection":
        self._connection.__enter__()
        return self
    def __exit__(self, exc_type, exc, traceback):
        return self._connection.__exit__(exc_type, exc, traceback)
    def execute(self, query: str, params: tuple[Any, ...] | list[Any] = ()):
        sql = query
        ignore_insert = "INSERT OR IGNORE" in sql.upper()
        if ignore_insert:
            sql = re.sub(r"INSERT\s+OR\s+IGNORE\s+INTO", "INSERT INTO", sql, flags=re.IGNORECASE)
        for table in _TABLES:
            sql = re.sub(rf"\b{re.escape(table)}\b", f"public.mk_{table}", sql, flags=re.IGNORECASE)
        sql = sql.replace("?", "%s")
        if ignore_insert:
            sql = sql.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"
        values = tuple(params or ())
        if re.search(r"UPDATE\s+public\.mk_guild_settings\s+SET\s+(welcome_enabled|xp_enabled)\s*=", sql, re.IGNORECASE) and values:
            values = (bool(values[0]), *values[1:])
        return self._connection.execute(sql, values)

def get_connection():
    """Return a context-managed SQLite or Supabase PostgreSQL connection."""
    if DATABASE_BACKEND == "sqlite":
        import sqlite3
        return sqlite3.connect(DB_PATH)
    if not SUPABASE_DB_URL:
        raise RuntimeError("DATABASE_BACKEND=supabase exige SUPABASE_DB_URL (URI PostgreSQL privée du projet MK Arena).")
    return SupabaseConnection(psycopg.connect(SUPABASE_DB_URL, connect_timeout=10))
