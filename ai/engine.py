import re
from .intent import detect_intent

class NovaEngine:
    def __init__(self, knowledge, context):
        self.knowledge = knowledge
        self.context = context

    def is_called(self, text: str) -> bool:
        return bool(re.search(r"(?<![\w])nova(?![\w])", text, flags=re.IGNORECASE))

    def remove_call(self, text: str) -> str:
        return re.sub(r"(?<![\w])nova(?![\w])\s*[:,\-]?\s*", "", text, count=1, flags=re.IGNORECASE)

    def respond(self, user_id: int, guild_id: int, text: str) -> str:
        intent = detect_intent(text)
        if intent == "greeting":
            return "Tranquille 😎 Je suis là. Qu'est-ce qu'on fait ?"
        if intent == "tournament":
            return self._tournament_answer(text, guild_id)
        if intent == "codm":
            return self._codm_answer(text)
        if intent == "general":
            return self._general_answer(text)
        return "Je t'écoute 😎 Reformule si tu veux que je cherche une information précise."

    def _tournament_answer(self, text, guild_id):
        results = self.knowledge.search_tournaments(text, guild_id)
        if not results:
            return "Je n'ai pas trouvé cette information dans les données disponibles des tournois."
        if len(results) > 1 and not any(word in text.lower() for word in [r["name"].lower() for r in results]):
            names = ", ".join(r["name"] for r in results[:5])
            return f"Tu parles de quel tournoi ? 👀 J'ai trouvé : {names}"
        best = results[0]
        details = self.knowledge.get_tournament_details(best["id"])
        return format_tournament_answer(text, details)

    def _codm_answer(self, text):
        t = text.lower()
        if "scrim" in t:
            return "Un scrim est un match d'entraînement compétitif entre équipes, généralement organisé pour travailler la stratégie, la communication et les automatismes."
        if "hardpoint" in t or "point stratégique" in t:
            return "Le Hardpoint est un mode objectif : les équipes se disputent des zones qui rapportent des points. En compétitif, les rotations et le contrôle des zones sont essentiels."
        if "r&d" in t or "recherche" in t and "destruction" in t:
            return "La Recherche & Destruction oppose deux équipes avec des manches à objectif. La communication, les trades, les timings et la gestion des vies sont particulièrement importants."
        return "Je peux t'aider sur CODM : armes, modes, stratégie, scrims, compétitif, rotations et bien plus. Donne-moi le sujet précis. 🎮"

    def _general_answer(self, text):
        t = text.lower()
        if any(x in t for x in ["ça va", "ca va", "vas", "comment tu"]):
            return "Tranquille 😎 Tout fonctionne de mon côté."
        if "qui es-tu" in t or "qui es tu" in t:
            return "Je suis NOVA, l'IA de MK ARENA. Je peux discuter, chercher des infos du serveur et apprendre des connaissances que le staff m'autorise à retenir."
        if "trou noir" in t:
            return "Un trou noir est une région de l'espace où la gravité est tellement intense qu'au-delà de son horizon des événements, même la lumière ne peut plus s'échapper."
        return "Je peux essayer de t'aider. Pour l'instant, ma v0.1 connaît surtout les bases de MK ARENA, les tournois et quelques sujets CODM."

def format_tournament_answer(question: str, d: dict) -> str:
    q = question.lower()
    name = d.get("name", "ce tournoi")
    if any(x in q for x in ["règle", "regle", "règlement", "reglement", "respecter"]):
        rules = d.get("rules") or "Aucune règle n'a encore été indexée."
        return f"📜 Règles de **{name}**\n{rules}"
    if any(x in q for x in ["prize", "récompense", "recompense", "gain"]):
        return f"💰 Pour **{name}**, le prizepool indiqué est : **{d.get('prizepool') or 'non renseigné'}**."
    if any(x in q for x in ["équipe", "equipe", "team", "combien"]):
        if d.get("teams"):
            return f"👥 **{name}** compte actuellement **{d['teams']} équipes** selon les informations indexées."
    if any(x in q for x in ["date", "quand", "commence", "début", "debut"]):
        return f"📅 **{name}** : {d.get('date') or 'date non renseignée'}."
    if any(x in q for x in ["format", "bo3", "bo5"]):
        return f"🎮 Format de **{name}** : {d.get('format') or 'non renseigné'}."
    parts = [f"🏆 **{name}**"]
    for label, key in [("Date", "date"), ("Équipes", "teams"), ("Prizepool", "prizepool"), ("Format", "format"), ("Statut", "status")]:
        if d.get(key):
            parts.append(f"**{label} :** {d[key]}")
    return "\n".join(parts) if len(parts) > 1 else f"J'ai trouvé **{name}**, mais peu d'informations sont encore indexées."
