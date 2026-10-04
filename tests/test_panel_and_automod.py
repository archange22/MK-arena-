import pytest
from memory.database import Database
from security.automod import AutoModManager
from features.leveling import LevelingManager

def test_guild_settings_and_warns():
    db = Database(":memory:")
    db.initialize()
    
    # Check default settings
    s = db.get_guild_settings(123)
    assert s["welcome_enabled"] == 0
    assert s["glados_core"] == "curiosity"
    
    # Save settings
    db.save_guild_settings(123, {"welcome_enabled": 1, "autorole_id": 9999, "glados_core": "anger"})
    s2 = db.get_guild_settings(123)
    assert s2["welcome_enabled"] == 1
    assert s2["autorole_id"] == 9999
    assert s2["glados_core"] == "anger"

    # Warns
    w_id = db.add_warn(123, 456, 789, "Spam abusif")
    assert w_id > 0
    warns = db.get_warns(123, 456)
    assert len(warns) == 1
    assert warns[0]["reason"] == "Spam abusif"
    assert db.count_warns(123) == 1

    db.clear_warns(123, 456)
    assert len(db.get_warns(123, 456)) == 0

def test_automod():
    automod = AutoModManager()
    settings = {
        "automod_invites": 1,
        "automod_links": 1,
        "automod_caps": 1,
        "automod_blacklist": "ez, arnaque",
    }

    # Invite test
    violation, reason = automod.check_message(1, "Rejoins mon discord discord.gg/abcdef !", settings)
    assert violation is True
    assert "Anti-Pub" in reason

    # Link test
    violation, reason = automod.check_message(1, "Regarde ce site https://google.com", settings)
    assert violation is True
    assert "Anti-Liens" in reason

    # Caps test
    violation, reason = automod.check_message(1, "BONJOUR JE HURLE ICI TOTALEMENT", settings)
    assert violation is True
    assert "Anti-Majuscules" in reason

    # Blacklist test
    violation, reason = automod.check_message(1, "Ce match était trop ez !", settings)
    assert violation is True
    assert "prohibé" in reason

    # Clean message
    violation, reason = automod.check_message(1, "Salut tout le monde, prêt pour la ranked ?", settings)
    assert violation is False

def test_leveling():
    db = Database(":memory:")
    db.initialize()
    lvl = LevelingManager(db)

    xp, level, level_up = lvl.process_message(10, 20, rate=1.0)
    assert xp == 15
    assert level == 0
    
    # Info
    info = lvl.get_rank_info(10, 20)
    assert info["xp"] == 15
    assert info["level"] == 0
    assert info["rank"] == 1
