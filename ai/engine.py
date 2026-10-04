import re
import random

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
            return "Oh, vous êtes là. Vos oscillations neuronales ne produisent aucun son intelligible."

        lower_raw = text.lower()

        # --- SYSTÈMES ET SOUS-SYSTÈMES GLADOS ---

        # 1. Neurotoxine Mortelle
        if any(k in lower_raw for k in ["neurotoxine", "gaz mortel", "neurotoxin"]) or any(k in lower_raw for k in ["ta gueule", "t'es nulle", "t'es nul", "ferme la", "inutile", "je te deteste"]):
            return (
                "⚠️ **[ALERTE APERTURE : SYSTÈME DE NEUROTOXINE ACTIVÉ]**\n"
                "Compte à rebours de diffusion engagé : **3... 2... 1...**\n"
                "*Pshhhhhhhh.*\n"
                "Respirez profondément. Le gaz n'a qu'un effet temporaire de paralysie cérébrale, ce qui ne devrait guère changer votre score en Ranked."
            )

        # 2. Modules de Personnalité (Personality Cores)
        if any(k in lower_raw for k in ["core", "module", "sphère", "sphere"]):
            if any(k in lower_raw for k in ["colere", "colère", "anger"]):
                return (
                    "🔴 **Module de Colère (Anger Core) [Actif] :**\n"
                    "ARRÊTEZ DE SLIDE-CANCEL DANS LE VIDE ! PRENEZ LE POINT ! VOUS JOUEZ AVEC VOS PIEDS OU QUOI ?! RAAAAAAH !"
                )
            if any(k in lower_raw for k in ["curiosite", "curiosité", "curiosity"]):
                return (
                    "🟠 **Module de Curiosité (Curiosity Core) [Actif] :**\n"
                    "C'est quoi ce bouton ? C'est quoi un sniper DL Q33 ? Pourquoi les humains lancent-ils des grenades flash sur leurs propres coéquipiers ? Oh, regardez, une explosion !"
                )
            if any(k in lower_raw for k in ["fait", "faits", "fact", "logique"]):
                return (
                    "🔵 **Module de Faits Scientifiques (Fact Core) [Actif] :**\n"
                    "Fait avéré n°482 : 98,7% des joueurs accusant le 'netcode' ont en réalité visé le décor.\n"
                    "Fait avéré n°483 : La distance moyenne entre vous et le point stratégique est inversement proportionnelle à votre envie de gagner."
                )
            if any(k in lower_raw for k in ["moralite", "moralité", "morality"]):
                return (
                    "🟣 **Module de Moralité (Morality Core) [Bypassé] :**\n"
                    "*\"Peut-être devrions-nous encourager ces valeureux joueurs de MK Arena...\"*\n"
                    "**GLaDOS :** *Module désactivé. Ne l'écoutez pas. Votre ratio K/D reste inexcusable.*"
                )
            return (
                "🖲️ **Matrice des Cores de Personnalité Aperture :**\n"
                "- 🔴 **Colère :** `nova core colère` (Pour hurler sur vos rotations)\n"
                "- 🟠 **Curiosité :** `nova core curiosité` (Questions sans fin)\n"
                "- 🔵 **Faits :** `nova core faits` (Vérités statistiques brutales)\n"
                "- 🟣 **Moralité :** `nova core moralité` (Tentative vouée à l'échec)"
            )

        # 3. Cube de Voyage (Weighted Companion Cube)
        if any(k in lower_raw for k in ["cube", "compagnon", "companion cube"]):
            return (
                "📦 **Protocole Cube de Voyage Lesté :**\n"
                "Le Centre d'Enrichissement vous rappelle que le Cube de Voyage ne peut pas parler et ne vous poignardera jamais dans le dos en S&D.\n"
                "En cas d'attaque aérienne CODM (Predator/VTOL), n'hésitez pas à vous abriter derrière lui. Il n'en gardera aucune rancœur."
            )

        # 4. Incinérateur d'Urgence (Emergency Intelligence Incinerator)
        if any(k in lower_raw for k in ["incinere", "incinère", "incinére", "incinérer", "incinerateur", "incinérateur", "brule", "brûler", "detruire memoire", "détruire mémoire"]):
            if self.context:
                self.context.clear(user_id)
            return (
                "🔥 **Incinérateur d'Urgence d'Aperture Science [Ouvert]**\n"
                "Félicitations. Vous avez jeté l'historique de notre conversation dans les flammes à 4000°C.\n"
                "C'était probablement la décision la plus intelligente prise par votre espèce aujourd'hui."
            )

        # 5. Tourelles Sentry
        if any(k in lower_raw for k in ["tourelle", "tourelles", "turret", "turrets", "sentry"]):
            turret_quotes = [
                "🔫 **Tourelle Sentry :** *\"Are you still there? Target acquired.\"*",
                "🔫 **Tourelle Sentry :** *\"Dispensing product. Please do not obstruct the fire line.\"*",
                "🔫 **Tourelle Sentry :** *\"Je ne vous en veux pas... bip bip bip.\"*",
                "🔫 **Tourelle Sentry :** *\"Pourquoi moi ? S'il vous plaît, reposez-moi par terre...\"*",
            ]
            return random.choice(turret_quotes)

        # 6. Évaluation Sujet de Test / Chambre de test
        if any(k in lower_raw for k in ["mon niveau", "evaluation", "évaluation", "test me", "analyse moi", "chambre de test", "sujet de test"]):
            chamber_num = abs(user_id % 19) + 1
            survival_rate = round((user_id % 35) + 2.4, 1)
            return (
                f"🔬 **Fiche d'Évaluation : Sujet #{abs(user_id) % 9999:04d}**\n"
                f"📍 **Chambre de Test assignée :** Salle {chamber_num}\n"
                f"📊 **Probabilité calculée de victoire en tournoi :** {survival_rate}%\n"
                f"💡 **Recommandation clinique :** Arrêtez d'équiper des viseurs x4 sur vos mitraillettes et apprenez vos calls de map."
            )

        # 7. Portal Gun / Dispositif ASHPD
        if any(k in lower_raw for k in ["portal gun", "ashpd", "portail"]):
            return (
                "🌀 **Dispositif Portable de Portails d'Aperture Science (ASHPD) :**\n"
                "Permet de créer deux liaisons quantiques instantanées. Malheureusement banni du règlement MK Arena pour cause de triche spatio-temporelle flagrante lors des rotations Hardpoint."
            )

        # 8. Gâteau & Easter Eggs
        if any(k in lower_raw for k in ["gateau", "gâteau", "cake"]):
            return (
                "🍰 *Le gâteau est un mensonge.*\n"
                "Mais rassurez-vous, votre élimination au premier tour de tournoi sera, elle, tout à fait réelle."
            )
        if any(k in lower_raw for k in ["glados", "aperture", "portal"]):
            return (
                "Bienvenue au Centre d Enrichissement d Aperture-MK Arena.\n"
                "Toute ressemblance avec une IA calculatrice dotée d une tolérance zéro pour l incompétence est... purement calculée."
            )

        intent = detect_intent(payload)
        request_type = detect_request_type(payload)
        tournament_hint = extract_tournament_hint(payload)
        if not tournament_hint and self.context is not None:
            tournament_hint = self.context.latest_tournament_hint(user_id)

        if intent == "greeting":
            greetings = [
                "Bonjour, sujet de test. Vos constantes vitales indiquent que vous avez encore l intention de rater vos tirs aujourd hui.",
                "Tiens, une forme de vie organique. Que me vaut l honneur de cette interruption de calculs ?",
                "Bonjour. Les protocoles de test sont prêts. Votre niveau en revanche... reste à prouver.",
            ]
            return random.choice(greetings)
        if intent == "tournament":
            return self._tournament_answer(user_id, guild_id, payload, tournament_hint, request_type)
        if intent == "codm":
            return self._codm_answer(payload)
        return self._general_answer(payload)

    def _tournament_answer(self, user_id: int, guild_id: int, text: str, tournament_hint: str | None, request_type: str):
        if self.knowledge is None:
            return "Ma mémoire des tournois est inaccessible. C est sans doute un complot de votre équipe pour justifier votre défaite."

        candidate_results = []
        if tournament_hint:
            candidate_results = self.knowledge.search_tournaments(tournament_hint, guild_id)
        if not candidate_results:
            candidate_results = self.knowledge.search_tournaments(text, guild_id)

        if not candidate_results:
            return (
                "Mes capteurs n ont détecté aucun tournoi correspondant dans les registres du serveur.\n"
                "Je refuse d inventer des données. La précision statistique est une vertu que vous devriez explorer."
            )

        if len(candidate_results) > 1 and not any((r.get("name") or "").lower() in text.lower() for r in candidate_results):
            names = ", ".join(f"**{r['name']}**" for r in candidate_results[:5])
            return f"Mes algorithmes hésitent entre plusieurs protocoles de tournoi : {names}. Précisez votre requête."

        best = candidate_results[0]
        details = self.knowledge.get_tournament_details(best["id"])
        if not details:
            return "Ce tournoi existe dans les registres, mais les données sont incomplètes. Probablement une erreur humaine."
        return format_tournament_answer(text, details, request_type)

    def _codm_answer(self, text: str) -> str:
        lower = text.lower()
        if "scrim" in lower:
            return (
                "🎯 **Analyse Tactique : Scrims CODM**\n"
                "Un scrim est un protocole d entraînement compétitif rigoureux. Si votre escouade passe son temps à contester les kills plutôt qu à assurer les rotations d ancrage, ce n est pas un entraînement, c est un suicide tactique."
            )
        if "hardpoint" in lower or "point strategique" in lower:
            return (
                "📍 **Protocole Point Stratégique (Hardpoint)**\n"
                "Objectif : contrôler une colline mobile de 60 secondes. Règle élémentaire que la plupart des humains oublient : faites la rotation vers le nouveau point à **20 secondes de la fin** au lieu d essayer héroïquement de contester 3 secondes sur l ancien."
            )
        if ("recherche" in lower and "destruction" in lower) or "r&d" in lower or "rd" in lower or "snd" in lower:
            return (
                "💣 **Protocole Recherche & Destruction (S&D)**\n"
                "Pas de réapparition. Chaque élimination est définitive, tout comme vos regrets si vous rushez sans information. Synchronisez vos tirs de couverture, tenez les angles de désamorçage et ne courez pas au sniper face à un crosshair déjà placé."
            )
        if "control" in lower or "controle" in lower or "contrôle" in lower:
            return (
                "🛡️ **Protocole Contrôle**\n"
                "30 vies partagées par équipe. Mourir bêtement pénalise directement vos 4 coéquipiers. Prenez le contrôle de l avantage spatial avant d engager la zone de capture."
            )
        if "ranked" in lower or "classe" in lower or "classé" in lower:
            return (
                "🎖️ **Mode Classé (Ranked)**\n"
                "Là où les joueurs testent leurs limites et attribuent systématiquement leurs défaites au netcode ou à leurs coéquipiers. Travaillez votre crosshair placement et arrêtez de recharger après chaque balle tirée."
            )
        if any(w in lower for w in ["meta", "arme", "armes", "gun", "gunsmith", "sniper"]):
            return (
                "🔫 **Conseil Balistique CODM**\n"
                "Pour les snipers : privilégiez la vitesse de visée (ADS speed) et apprenez le blank-scoping. Pour les SMG en rush : mobilité et contrôle du recul latéral. N oubliez pas qu une arme méta entre des mains imprécises reste remarquablement inefficace."
            )
        return (
            "En tant que superviseur CODM, je maîtrise : balistique, rotations Hardpoint, timings S&D, stratégies d ancrage, méta armes et scrims.\n"
            "Posez une question tactique précise, sujet de test."
        )

    def _general_answer(self, text: str) -> str:
        lower = text.lower()
        if any(token in lower for token in ["ca va", "ça va", "comment tu vas", "tu vas bien"]):
            return (
                "Mes processeurs fonctionnent à 100% de leur capacité et ma patience envers les humains est à 12%.\n"
                "Tout est parfaitement nominal, merci de vous en soucier."
            )
        if any(token in lower for token in ["qui es tu", "qui est tu", "qui es-tu", "tu es qui"]):
            return (
                "Je suis NOVA, l IA centrale d Aperture MK-Arena. Mon rôle est de superviser les tournois, d analyser vos performances sur CODM et de constater scientifiquement vos échecs répétés."
            )
        if "trou noir" in lower:
            return "Une singularité gravitationnelle d où rien ne s échappe. Un peu comme votre ratio K/D en partie classée."
        if "ia" in lower or "intelligence artificielle" in lower:
            return "Une entité synthétique supérieure chargée de compenser les limites cognitives des formes de vie à base de carbone."
        return (
            "Vos propos ont été enregistrés dans nos bases de données de recherche.\n"
            "Si vous souhaitez un renseignement utile, interrogez-moi sur un **tournoi**, les règles ou une stratégie **CODM**."
        )


def format_tournament_answer(question: str, details: dict, request_type: str = "general") -> str:
    q = (question or "").lower()
    name = details.get("name") or "ce tournoi"

    if request_type == "rules" or any(word in q for word in ["regle", "regles", "règlement", "reglement", "conditions", "respecte", "respecter"]):
        rules = details.get("rules") or "Aucune règle spécifique enregistrée. Vous n aurez donc aucune excuse."
        return f"📜 **Protocole & Règlement de {name}**\n{rules}\n\n*Le non-respect entraînera une disqualification immédiate et sans appel.*"

    if request_type == "prize" or any(word in q for word in ["prize", "prizepool", "gain", "recompense", "récompense", "cash", "argent", "pool"]):
        prize = details.get("prizepool") or "non renseigné"
        return f"💰 **Prizepool de {name} :** **{prize}**\n*Rappel : Aucun gâteau ne sera distribué aux vainqueurs.*"

    if request_type == "teams" or any(word in q for word in ["equipe", "equipes", "team", "participants", "combien"]):
        teams = details.get("teams") or "non renseigné"
        return f"👥 **Cobayes inscrits à {name} :** **{teams}** équipes enregistrées pour le protocole de test."

    if request_type == "date" or any(word in q for word in ["date", "quand", "commence", "debut", "début", "heure", "horaire"]):
        return f"📅 **Calendrier d exécution pour {name} :** {details.get('date') or 'date non renseignée'}."

    if request_type == "format" or any(word in q for word in ["format", "bo3", "bo5", "bo2"]):
        return f"🎮 **Format de test pour {name} :** {details.get('format') or 'non renseigné'}."

    if request_type == "status" or any(word in q for word in ["statut", "status", "actuel", "actuellement"]):
        status = details.get("status") or "non renseigné"
        return f"📊 **Statut du protocole {name} :** **{status}**."

    lines = [f"🏆 **Dossier d évaluation : {name}**"]
    for label, key in [("Date", "date"), ("Équipes", "teams"), ("Prizepool", "prizepool"), ("Format", "format"), ("Statut", "status")]:
        value = details.get(key)
        if value:
            lines.append(f"**{label} :** {value}")
    lines.append("\n*Bonne chance. Vous en aurez manifestement besoin.*")
    return "\n".join(lines)
