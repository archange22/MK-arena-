from ai.intent import detect_intent, detect_request_type, extract_tournament_hint


def test_detect_intent_tournament():
    assert detect_intent("nova c quoi les regle du squid game") == "tournament"
    assert detect_intent("nova explique moi le hardpoint") == "codm"
    assert detect_intent("nova bonjour") == "greeting"


def test_detect_request_type():
    assert detect_request_type("nova le prizepool du squid game") == "prize"
    assert detect_request_type("nova donne moi les regles") == "rules"


def test_extract_tournament_hint():
    assert extract_tournament_hint("nova le squid game il commence quand") == "mk squid game"
    assert extract_tournament_hint("nova world cup") == "mk world cup"
