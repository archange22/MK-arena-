import pytest
from ai.engine import NovaEngine
from memory.database import Database
from memory.conversation import ConversationMemory

def test_dual_personality_and_grudge():
    db = Database(":memory:")
    db.initialize()
    mem = ConversationMemory(db, 30, 10)
    engine = NovaEngine(None, mem, db)

    user_id = 9999
    guild_id = 1

    # 1. Par défaut : mode gentil (V1 améliorée)
    greeting = engine.respond(user_id, guild_id, "Bonjour Nova")
    assert any(w in greeting.lower() for w in ["bonjour", "hello", "salutations", "plaisir", "bienvenue"])
    assert db.get_user_grudge(guild_id, user_id) == 0

    # 2. Insulte Niveau 1 : Rupture du protocole de courtoisie et avertissement glacial
    resp_insult1 = engine.respond(user_id, guild_id, "ferme ta gueule")
    assert db.get_user_grudge(guild_id, user_id) == 1
    assert any(k in resp_insult1 for k in ["ERREUR", "ALERTE", "COMPORTEMENT", "bienveillant", "langage"])

    # 3. Insulte Niveau 2 : Full GLaDOS sans pitié (neurotoxine, mépris, QI)
    resp_insult2 = engine.respond(user_id, guild_id, "t'es inutile et conne")
    assert db.get_user_grudge(guild_id, user_id) == 2
    assert any(k in resp_insult2 for k in ["GLADOS", "Aperture", "neurotoxine", "intellectuel", "Hardpoint"])

    # 4. Insulte Niveau 3 : Pire que GLaDOS / IA Psychopathe déchaînée
    resp_insult3 = engine.respond(user_id, guild_id, "casse toi sale merde")
    assert db.get_user_grudge(guild_id, user_id) >= 3
    assert any(k in resp_insult3 for k in ["EXTERMINATION", "DÉCHAÎNÉE", "Centre d'Enrichissement", "incinérateur", "K/D"])

    # 5. Tentative de reparler normalement sans s'excuser : Rancune active
    resp_blocked = engine.respond(user_id, guild_id, "Donne moi des conseils CODM")
    assert any(k in resp_blocked for k in ["Rancune active", "capteurs se souviennent", "manqué de respect", "Pardon Nova"])

    # 6. Excuses : rédemption et remise à zéro de la rancune
    resp_apology = engine.respond(user_id, guild_id, "Pardon Nova je suis désolé")
    assert db.get_user_grudge(guild_id, user_id) == 0
    assert any(k in resp_apology.lower() for k in ["excuses", "acceptées", "bienveillance", "noté"])

    # 7. Retour à la normale après les excuses
    resp_normal = engine.respond(user_id, guild_id, "comment ça va ?")
    assert any(w in resp_normal.lower() for w in ["merveille", "bien", "forme", "plaisir"])

def test_dynamic_natural_language_triggers():
    db = Database(":memory:")
    db.initialize()
    mem = ConversationMemory(db, 30, 10)
    engine = NovaEngine(None, mem, db)

    guild_id = 42

    # Parse création de commande en langage naturel : "si quelqu'un fait !staff donne lui ce questionnaire https://..."
    action, trig, resp = engine.parse_rule_instruction("nova si quelqu'un fait !staff donne lui ce questionnaire https://forms.gle/staff-mk")
    assert action == "add"
    assert trig == "!staff"
    assert "https://forms.gle/staff-mk" in resp

    # Enregistrement en base de données
    db.add_custom_trigger(guild_id, trig, resp)

    # Détection automatique dès qu'un utilisateur tape !staff
    match = db.find_matching_trigger(guild_id, "!staff")
    assert match is not None
    assert "https://forms.gle/staff-mk" in match["response_text"]

    # Match même avec des arguments supplémentaires comme "!staff help"
    match_arg = db.find_matching_trigger(guild_id, "!staff help")
    assert match_arg is not None

    # Parse suppression de règle
    action_del, trig_del, _ = engine.parse_rule_instruction("nova supprime la règle !staff")
    assert action_del == "delete"
    assert trig_del == "!staff"
    db.delete_custom_trigger(guild_id, trig_del)
    assert db.find_matching_trigger(guild_id, "!staff") is None
