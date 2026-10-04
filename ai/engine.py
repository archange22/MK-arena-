import re

from ai.intent import detect_intent, detect_request_type, extract_tournament_hint


class NovaEngine:
    def __init__(self, knowledge, context):
        self.knowledge = knowledge
        self.context = context

    def is_called(self, text: str) -> bool:
        if not text:
            return False
        return bool(re.search(r"(?<![a-z0-9])nova(?![a-z0-9])", text, flags=re.IGNORECASE))

    def remove_call(self, text: str) -> str:
        cleaned = re.sub(
            r"(?<![a-z0-9])nova(?![a-z0-9])\s*[:\-]?\s*",
            "",
            text,
            count=1,
            flags=re.IGNORECASE,
        )
        return cleaned.strip()

    def respond(self, user_id: int, guild_id: int, text: str, reference_context: str | None = None) -> str:
        if self.context is not None:
            recent_context = self.context.build_summary(user_id)
        else:
            recent_context = ""

        context_parts = [part for part in [recent_context, reference_context, text] if part and str(part).strip()]
        payload = " ".join(str(part).strip() for part in context_parts)
        if not payload:
            return "Oui ? 😎"

        intent = detect_intent(payload)
        request_type = detect_request_type(payload)
        tournament_hint = extract_tournament_hint(payload)
        if not tournament_hint and self.context is not None:
            tournament_hint = self.context.latest_tournament_hint(user_id)

        if intent == "greeting":
            return "Tranquille 😎 Je suis opérationnelle. Qu'est-ce qu'on fait ?"
        if intent == "tournament":
            return self._tournament_answer(user_id, guild_id, payload, tournament_hint, request_type)
        if intent == "codm":
            return self._codm_answer(payload)
        return self._general_answer(payload)

    def _tournament_answer(self, user_id: int, guild_id: int, text: str, tournament_hint: str | None, request_type: str):
        if self.knowledge is None:
            return "Je n'ai pas de mémoire de tournoi disponible pour le moment."

        candidate_results = []
        if tournament_hint:
            candidate_results = self.knowledge.search_tournaments(tournament_hint, guild_id)
        if not candidate_results:
            candidate_results = self.knowledge.search_tournaments(text, guild_id)

        if not candidate_results:
            return "Je n'ai pas trouvé cette information dans les données disponibles du serveur. Je préfère ne pas l'inventer."

        if len(candidate_results) > 1 and not any((r.get("name") or "").lower() in text.lower() for r in candidate_results):
            names = ", ".join(r["name"] for r in candidate_results[:5])
            return f"Tu parles de quel tournoi ? 👀 J'ai trouvé : {names}"

        best = candidate_results[0]
        details = self.knowledge.get_tournament_details(best["id"])
        if not details:
            return "J'ai trouvé un tournoi, mais il n'y a pas encore assez d'informations pour te répondre proprement."
        return format_tournament_answer(text, details, request_type)

    def _codm_answer(self, text: str) -> str:
        lower = text.lower()
        if "scrim" in lower:
            return "Un scrim est un match d'entraînement compétitif. C'est le moment de tester une stratégie, une rotation, une composition ou une coordination d'équipe."
        if "hardpoint" in lower:
            return "Le Hardpoint consiste à contrôler une zone qui évolue. La rotation et le contrôle des points sont essentiels."
        if ("recherche" in lower and "destruction" in lower) or "r&d" in lower or "rd" in lower:
            return "La Recherche & Destruction est un mode très axé sur la communication, les trades, les timings et la gestion des vies."
        if "control" in lower or "controle" in lower or "contrôle" in lower:
            return "Le Contrôle tourne autour des zones à prendre et à défendre. Le timing de pression et la coordination de la team sont primordiaux."
        if "ranked" in lower:
            return "Le Ranked est le mode compétitif où les performances et la cohésion sont décisives."
        return "Je peux t'aider sur CODM : armes, modes, scrims, rotations, stratégies, Ranked et tournois. Donne-moi un sujet précis. 🎮"

    def _general_answer(self, text: str) -> str:
        lower = text.lower()
        if any(token in lower for token in ["ca va", "ça va", "comment tu vas", "tu vas bien"]):
            return "Tranquille 😎 Tout est opérationnel. Et toi ?"
        if any(token in lower for token in ["qui es tu", "qui est tu", "qui es-tu", "tu es qui"]):
            return "Je suis NOVA, l'IA de MK ARENA. Je peux discuter, répondre à des questions, chercher des infos du serveur et aider sur les tournois et sur CODM."
        if "trou noir" in lower:
            return "Un trou noir est une région de l'espace où la gravité est si intense que même la lumière ne peut plus s'échapper."
        if "ia" in lower or "intelligence artificielle" in lower:
            return "Une IA traite des données pour reconnaître des schémas et répondre à des demandes. Ici, le projet reste modulaire et localement extensible."
        return "Je peux t'aider sur plusieurs sujets. Si tu veux, on peut parler des tournois, du CODM, du serveur, ou d'un autre sujet."


def format_tournament_answer(question: str, details: dict, request_type: str = "general") -> str:
    q = (question or "").lower()
    name = details.get("name") or "ce tournoi"

    if request_type == "rules" or any(word in q for word in ["regle", "regles", "règlement", "reglement", "conditions", "respecte", "respecter"]):
        rules = details.get("rules") or "Aucune règle n'a encore été indexée pour ce tournoi."
        return f"📜 Règles de **{name}**\n{rules}"

    if request_type == "prize" or any(word in q for word in ["prize", "prizepool", "gain", "recompense", "récompense", "cash", "argent", "pool"]):
        prize = details.get("prizepool") or "non renseigné"
        return f"💰 Pour **{name}**, le prizepool indiqué est : **{prize}**."

    if request_type == "teams" or any(word in q for word in ["equipe", "equipes", "team", "participants", "combien"]):
        teams = details.get("teams") or "non renseigné"
        return f"👥 **{name}** compte actuellement **{teams}** selon les informations indexées."

    if request_type == "date" or any(word in q for word in ["date", "quand", "commence", "debut", "début", "heure", "horaire"]):
        return f"📅 **{name}** : {details.get('date') or 'date non renseignée'}."

    if request_type == "format" or any(word in q for word in ["format", "bo3", "bo5", "bo2"]):
        return f"🎮 Format de **{name}** : {details.get('format') or 'non renseigné'}."

    if request_type == "status" or any(word in q for word in ["statut", "status", "actuel", "actuellement"]):
        status = details.get("status") or "non renseigné"
        return f"📊 Statut de **{name}** : **{status}**."

    lines = [f"🏆 **{name}**"]
    for label, key in [("Date", "date"), ("Équipes", "teams"), ("Prizepool", "prizepool"), ("Format", "format"), ("Statut", "status")]:
        value = details.get(key)
        if value:
            lines.append(f"**{label} :** {value}")
    return "\n".join(lines) if len(lines) > 1 else f"J'ai trouvé **{name}**, mais peu d'informations sont encore indexées pour le moment."
