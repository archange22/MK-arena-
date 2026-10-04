from ai.engine import NovaEngine
from memory.conversation import ConversationMemory
from memory.database import Database

def test_glados_systems():
    db = Database(":memory:")
    db.initialize()
    mem = ConversationMemory(db, 30, 10)
    engine = NovaEngine(None, mem)

    # 1. Neurotoxine
    res_neuro = engine.respond(1234, 1, "lance la neurotoxine")
    assert "NEUROTOXINE" in res_neuro

    # 2. Cores
    assert "Colère" in engine.respond(1234, 1, "nova core colère")
    assert "Curiosité" in engine.respond(1234, 1, "nova core curiosité")
    assert "Faits" in engine.respond(1234, 1, "nova core faits")
    assert "Moralité" in engine.respond(1234, 1, "nova core moralité")

    # 3. Cube de voyage
    assert "Cube de Voyage" in engine.respond(1234, 1, "où est le compagnon cube ?")

    # 4. Incinérateur
    assert "Incinérateur d'Urgence" in engine.respond(1234, 1, "incinère nos messages")

    # 5. Tourelles
    assert "Tourelle Sentry" in engine.respond(1234, 1, "active la tourelle")

    # 6. Évaluation
    assert "Fiche d'Évaluation" in engine.respond(1234, 1, "analyse mon niveau")

    # 7. Portal gun
    assert "ASHPD" in engine.respond(1234, 1, "donne moi le portal gun")

    # 8. Gâteau
    assert "mensonge" in engine.respond(1234, 1, "le gâteau arrive quand ?")
