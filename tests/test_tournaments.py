from ai.intent import detect_intent

def test_rules_variants():
    for text in [
        "nova donne les règles",
        "nova c'est quoi le règlement",
        "nova on doit respecter quoi",
    ]:
        assert detect_intent(text) == "tournament"
