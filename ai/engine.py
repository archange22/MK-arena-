import re

from ai.intent import detect_intent, extract_tournament_hint


class NovaEngine:
    def __init__(self, knowledge, context):
        self.knowledge = knowledge
        self.context = context

    def is_called(self, text: str) -> bool:
        if not text:
            return False
        return bool(re.search(r"(?<![a-zà-ÿ])nova(?![a-zà-ÿ])", text, flags=re.IGNORECASE))

    def remove_call(self, text: str) -> str:
        cleaned = re.sub(
            r"(?<![a-zà-ÿ])nova(?![a-zà-ÿ])\s*[:\-]?\s*",
            "",
            text,
            count=1,
            flags=re.IGNORECASE,
        )
        return cleaned.strip()

    def respond(self, user_id: int, guild_id: int, text: str, reference_context: str | None = None) -> str:
        base_text = text.strip()
        if reference_context:
            base_text = f"{reference_context} {base_text}".strip()

        if not base_text:
            return "Oui ? 😎"

        intent = detect_intent(base_text)
        tournament_hint = extract_tournament_hint(base_text)
        if not tournament_hint and self.context is not None and hasattr(self.context, "latest_tournament_hint"):
            tournament_hint = self.context.latest_tournament_hint(user_id)

        if intent == "greeting":
            return "Tranquille 😎 Je suis opérationnelle. Qu'est-ce qu'on fait ?"
        if intent == "tournament":
            return self._tournament_answer(user_id, guild_id, base_text, tournament_hint)
        if intent == "codm":
            return self._codm_answer(base_text)
        return self._general_answer(base_text)

    def _tournament_answer(self, user_id: int, guild_id: int, text: str, tournament_hint: str | None):
        if self.knowledge is None:
            return "Je n'ai pas de mémoire de tournoi disponible pour le moment."

        results = self.knowledge.search_tournaments(text, guild_id)
        if tournament_hint:
            exact = self.knowledge.search_tournaments(tournament_hint, guild_id)
            if exact:
                results = exact

        if not results:
            return "Je n'ai pas trouvé cette information dans les données disponibles du serveur. Je préfère ne pas l'inventer."

        if len(results) > 1 and not any((r["name"] or "").lower() in text.lower() for r in results):
            names = ", ".join(r["name"] for r in results[:5])
            return f"Tu parles de quel tournoi ? 👀 J'ai trouvé : {names}"

        best = results[0]
        details = self.knowledge.get_tournament_details(best["id"])
        return format_tournament_answer(text, details)

    def _codm_answer(self, text: str) -> str:
        lower = text.lower()
        if "scrim" in lower:
            return "Un scrim est un match d'entraînement compétitif. C'est le moment de tester un plan, une rotation ou un stratagème avant le vrai match."
        if "hardpoint" in lower:
            return "Le Hardpoint, c'est un mode où les deux équipes doivent contrôler une zone qui bouge. La rotation, le timing et l'occupation de la zone sont essentiels."
        if ("recherche" in lower and "destruction" in lower) or "r&d" in lower or "rd" in lower:
            return "La Recherche & Destruction est un mode objectif. Une bonne communication, le trade et le timing des entrées peuvent faire toute la différence."
        if "control" in lower or "contrôle" in lower:
            return "Le Contrôle consiste à prendre et défendre des zones. Le positionnement et le timing de la push sont très importants."
        if "ranked" in lower:
            return "Le Ranked, c'est le mode compétitif où les performances comptent. La cohésion d'équipe, les rotations et la gestion des talents sont essentiels."
        return "Je peux t'aider sur CODM : armes, classes, modes, scrims, stratégies, rotations, Ranked et tournois. Donne-moi un sujet précis. 🎮"

    def _general_answer(self, text: str) -> str:
        lower = text.lower()
        if any(token in lower for token in ["ca va", "ça va", "comment tu vas", "tu vas bien"]):
            return "Tranquille 😎 Tout est opérationnel. Et toi ?"
        if any(token in lower for token in ["qui es tu", "qui est tu", "qui es-tu", "tu es qui"]):
            return "Je suis NOVA, l'IA de MK ARENA. Je peux discuter, répondre aux questions, retrouver les infos du serveur et aider sur les tournois et le CODM."
        if "trou noir" in lower:
            return "Un trou noir est une région de l'espace où la gravité est si intense que même la lumière ne peut plus s'échapper."
        if "ia" in lower or "intelligence artificielle" in lower:
            return "Une IA est un système qui traite des données pour reconnaître des schémas, répondre à des questions ou aider à des tâches. Sur ce projet, je reste modulaire et localement extensible."
        if any(token in lower for token in ["idee", "idée", "video", "vidéo", "blague", "humour"]):
            return "D'accord, je peux t'aider. Donne-moi juste le type de contenu que tu veux : idée de vidéo, blague, ou autre sujet."
        return "Je peux t'aider sur plusieurs sujets. Si tu veux, on peut parler des tournois, du CODM, du serveur ou d'un autre sujet."


def format_tournament_answer(question: str, details: dict) -> str:
    q = (question or "").lower()
    name = details.get("name") or "ce tournoi"

    if any(word in q for word in ["regle", "regles", "règlement", "reglement", "règle", "respecte", "conditions"]):
        rules = details.get("rules") or "Aucune règle n'a encore ��té indexée pour ce tournoi."
        return f"📜 Règles de **{name}**\n{rules}"

    if any(word in q for word in ["prize", "prizepool", "gain", "recompense", "récompense", "cash", "pool"]):
        prize = details.get("prizepool") or "non renseigné"
        return f"💰 Pour **{name}**, le prizepool indiqué est : **{prize}**."

    if any(word in q for word in ["equipe", "equipes", "team", "participants", "combien"]):
        teams = details.get("teams") or "non renseigné"
        return f"👥 **{name}** compte actuellement **{teams}** selon les informations indexées."

    if any(word in q for word in ["date", "quand", "commence", "debut", "début", "heure", "horaire"]):
        return f"📅 **{name}** : {details.get('date') or 'date non renseignée'}."

    if any(word in q for word in ["format", "bo3", "bo5", "bo2"]):
        return f"🎮 Format de **{name}** : {details.get('format') or 'non renseigné'}."

    lines = [f"🏆 **{name}**"]
    for label, key in [("Date", "date"), ("Équipes", "teams"), ("Prizepool", "prizepool"), ("Format", "format"), ("Statut", "status")]:
        value = details.get(key)
        if value:
            lines.append(f"**{label} :** {value}")
    return "\n".join(lines) if len(lines) > 1 else f"J'ai trouvé **{name}**, mais peu d'informations sont encore indexées pour le moment."
