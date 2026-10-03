from ai.intent import detect_intent

def test_tournament_intent():
    assert detect_intent("nova donne les règles du tournoi") == "tournament"

def test_codm_intent():
    assert detect_intent("nova c'est quoi le hardpoint") == "codm"
