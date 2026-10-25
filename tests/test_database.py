import re
from database import DATABASE_BACKEND

def test_database_backend_is_explicitly_supported():
    assert DATABASE_BACKEND in {"sqlite", "supabase"}

def test_table_mapping_patterns():
    tables = {
        "warnings": "public.mk_warnings",
        "tournaments": "public.mk_tournaments",
        "tournament_registrations": "public.mk_tournament_registrations",
        "tournament_config": "public.mk_tournament_config",
        "guild_settings": "public.mk_guild_settings",
        "user_xp": "public.mk_user_xp",
        "tickets": "public.mk_tickets",
    }
    for old, new in tables.items():
        assert re.sub(rf"\b{old}\b", new, f"SELECT * FROM {old}") == f"SELECT * FROM {new}"
