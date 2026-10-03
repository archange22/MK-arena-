from memory.database import Database
from memory.knowledge import KnowledgeManager


def test_staff_learning_and_tournament_search():
    db = Database(":memory:")
    db.initialize()
    knowledge = KnowledgeManager(db)

    response = knowledge.learn("nova retiens que le MK SQUID GAME compte 16 équipes et le prizepool est de 250 €.", "staff:42", 1)
    assert "Compris" in response

    rows = knowledge.search_tournaments("mk squid game", 1)
    assert rows
    assert any((row["name"] or "").startswith("MK SQUID GAME") for row in rows)

    details = knowledge.get_tournament_details(rows[0]["id"])
    assert details["teams"] == "16"
