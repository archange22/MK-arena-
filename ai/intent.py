import re
import unicodedata

TOURNAMENT_ALIASES = {
    "mk squid game": "mk squid game",
    "squid game": "mk squid game",
    "mk world cup": "mk world cup",
    "world cup": "mk world cup",
    "mk champion league": "mk champion league",
    "champion league": "mk champion league",
    "squid": "mk squid game",
}


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = text.replace("’", "'").replace("“", '"').replace("”", '"')
    for source, target in {
        "ça": "ca",
        "c'est": "c est",
        "qu'est": "quest",
        "j'ai": "jai",
        "d'": " ",
        "l'": " ",
        "n'": " ",
    }.items():
        text = text.replace(source, target)
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def detect_intent(text: str) -> str:
    cleaned = normalize_text(text)
    if not cleaned:
        return "general"

    greeting_markers = [
        "bonjour", "salut", "hello", "yo", "ca va", "cava",
        "comment tu vas", "tu es la", "wsh", "bienvenue"
    ]
    if any(marker in cleaned for marker in greeting_markers):
        return "greeting"

    tournament_markers = [
        "tournoi", "tournois", "squid", "world cup", "champion league",
        "regle", "regles", "reglement", "règlement", "respecte", "respecter",
        "participer", "participation", "inscription",
        "prizepool", "prize", "equipe", "equipes", "team", "teams", "format", "date",
        "quand commence", "conditions", "comment fonctionne", "les regles",
        "on doit faire quoi", "c quoi les regles", "tournoi squid"
    ]
    if any(marker in cleaned for marker in tournament_markers):
        return "tournament"

    codm_markers = [
        "codm", "call of duty mobile", "hardpoint", "recherche et destruction",
        "r and d", "rd", "ranked", "control", "contrôle", "battle royale",
        "scrim", "rotation", "rotations", "arme", "loadout", "classe", "aim"
    ]
    if any(marker in cleaned for marker in codm_markers):
        return "codm"

    return "general"


def detect_request_type(text: str) -> str:
    cleaned = normalize_text(text)
    if not cleaned:
        return "general"

    for key, markers in {
        "rules": ["regle", "regles", "reglement", "conditions", "respecte", "respecter", "on doit faire quoi"],
        "teams": ["equipes", "equipe", "participants", "combien de equipes"],
        "prize": ["prizepool", "prize", "recompense", "gain", "cash", "argent"],
        "date": ["date", "quand", "commence", "debut", "heure", "horaire"],
        "format": ["format", "bo3", "bo5", "bo2"],
        "status": ["statut", "status", "en cours", "actuel", "actuellement"],
    }.items():
        if any(marker in cleaned for marker in markers):
            return key
    return "general"


def extract_tournament_hint(text: str) -> str | None:
    cleaned = normalize_text(text)
    if not cleaned:
        return None

    for alias, canonical in TOURNAMENT_ALIASES.items():
        if alias in cleaned:
            return canonical

    if "squid" in cleaned:
        return "mk squid game"

    return None
