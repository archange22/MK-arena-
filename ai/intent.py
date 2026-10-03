import re

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())

def detect_intent(text: str) -> str:
    t = normalize(text)
    if any(x in t for x in ["bonjour", "salut", "hello", "yo", "ça va", "ca va"]):
        return "greeting"
    tournament_words = [
        "tournoi", "tournois", "squid", "world cup", "champion league",
        "règle", "regle", "règlement", "reglement", "prize", "équipe", "equipe",
        "participer", "participation", "format", "bo3", "bo5", "scrim"
    ]
    if any(x in t for x in tournament_words):
        return "tournament"
    codm_words = ["codm", "call of duty mobile", "hardpoint", "r&d", "recherche et destruction", "ranked"]
    if any(x in t for x in codm_words):
        return "codm"
    return "general"
