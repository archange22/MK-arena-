import re
import unicodedata


def normalize_text(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKC", text).lower()
    normalized = normalized.replace("’", "'").replace("“", '"').replace("”", '"')
    replacements = {
        "ça": "ca",
        "c'est": "c est",
        "qu'est": "quest",
        "n'": " ",
        "d'": " ",
        "l'": " ",
        "j'ai": "jai",
        "j ai": "jai",
    }
    for src, dst in replacements.items():
        normalized = normalized.replace(src, dst)
    normalized = re.sub(r"[^a-z0-9\s\-]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def detect_intent(text: str) -> str:
    t = normalize_text(text)
    if not t:
        return "general"

    greeting_markers = [
        "bonjour", "salut", "hello", "yo", "ca va", "cava", "comment tu vas",
        "tu es la", "on va", "wsh"
    ]
    if any(marker in t for marker in greeting_markers):
        return "greeting"

    tournament_markers = [
        "tournoi", "tournois", "squid", "world cup", "champion league",
        "regle", "reglement", "regles", "participer", "inscription",
        "prizepool", "prize", "equipe", "equipes", "format", "statut",
        "date", "quand commence", "comment fonctionne", "conditions", "scrim",
        "team"
    ]
    if any(marker in t for marker in tournament_markers):
        return "tournament"

    codm_markers = [
        "codm", "call of duty mobile", "hardpoint", "recherche et destruction",
        "r and d", "rd", "ranked", "control", "battle royale", "scrim",
        "rotations", "aim", "classe", "arme", "loadout", "mode de jeu",
        "recherche destruction"
    ]
    if any(marker in t for marker in codm_markers):
        return "codm"

    return "general"


def extract_tournament_hint(text: str) -> str | None:
    t = normalize_text(text)
    candidates = [
        "mk squid game",
        "squid game",
        "mk world cup",
        "world cup",
        "mk champion league",
        "champion league",
        "squid",
        "mk arena",
    ]
    for candidate in candidates:
        if candidate in t:
            return candidate.title()
    return None
