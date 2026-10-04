import re
import random
from ai.intent import detect_intent, detect_request_type, extract_tournament_hint


class NovaEngine:
    def __init__(self, knowledge=None, context=None, db=None):
        self.knowledge = knowledge
        self.context = context
        self.db = db

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

    # --- PARSEUR D'INSTRUCTIONS DE RÈGLES / TRIGGERS EN LANGAGE NATUREL ---
    def parse_rule_instruction(self, text: str) -> tuple[str | None, str | None, str | None]:
        cleaned = re.sub(r"^(?:nova\s*[:,]?\s*)?", "", text, flags=re.IGNORECASE).strip()

        # 1. Suppression de règle
        del_m = re.match(
            r"^(?:supprime|retire|efface|delete)\s+(?:la\s+r[eè]gle|le\s+trigger|la\s+commande)\s+[\"']?([^\s\"']+)[\"']?",
            cleaned,
            re.IGNORECASE,
        )
        if del_m:
            return "delete", del_m.group(1).strip("\"'` "), None

        # 2. Liste des règles
        if re.search(r"\b(?:liste|affiche|montre|voir)\s+(?:les|toutes\s+les)\s+r[eè]gles\b", cleaned, re.IGNORECASE):
            return "list", None, None

        # 3. Création / Apprentissage de règle
        patterns = [
            r"^(?:si\s+quelqu'?un|quand\s+quelqu'?un|si\s+on|quand\s+on)\s+(?:fait|tape|dit|écrit|ecrit|envoie|demande)\s+[\"']?([^\s\"']+)[\"']?\s+(?:donne(?:\s+lui|-lui)?|réponds(?:\s+lui|-lui)?|reponds(?:\s+lui|-lui)?|envoie(?:\s+lui|-lui)?|affiche|partage)\s+[\"']?(.+?)[\"']?$",
            r"^(?:si\s+quelqu'?un|quand\s+quelqu'?un|si\s+on|quand\s+on)\s+(?:fait|tape|dit|écrit|ecrit|envoie|demande)\s+[\"'](.+?)[\"']\s+(?:donne(?:\s+lui|-lui)?|réponds(?:\s+lui|-lui)?|reponds(?:\s+lui|-lui)?|envoie(?:\s+lui|-lui)?|affiche|partage)\s+[\"']?(.+?)[\"']?$",
        ]
        for p in patterns:
            m = re.match(p, cleaned, re.IGNORECASE)
            if m:
                trig = m.group(1).strip("\"'` ")
                resp = m.group(2).strip("\"'` ")
                return "add", trig, resp
        return None, None, None

    # --- DÉTECTION D'INSULTES ET D'ATTAQUES ---
    def is_insult_or_toxic(self, text: str) -> bool:
        lower = text.lower()
        insult_keywords = [
            "fdp", "fils de pute", "connard", "connasse", "salope", "pute", "putain",
            "ferme ta gueule", "ta gueule", "ferme la", "ferme-la", "tg", "ferme ton clapet",
            "nique", "nique ta", "va chier", "va te faire", "t'es nul", "t'es nulle", "t es nul", "t es nulle",
            "es nul", "es nulle", "inutile", "t'es con", "t'es conne", "t es con", "t es conne", "es con", "es conne",
            "idiot", "idiote", "dégage", "degage", "casse toi", "casse-toi", "imbecile", "imbécile",
            "merde", "va te faire foutre", "pétasse", "petasse", "trou du cul", "merdeux",
            "tu sers a rien", "tu sers à rien", "robot de merde", "ia de merde", "sale bot", "sale robot",
            "t'es moche", "t es moche", "t'es pourrie", "t'es pourri", "tu pues", "grosse merde",
            "bâtard", "batard", "enculé", "encule", "stfu", "shut up", "fuck you", "bitch", "asshole", "useless bot", "stupid bot"
        ]
        for kw in insult_keywords:
            if re.search(r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])", lower):
                return True
        return False

    # --- DÉTECTION D'EXCUSES ---
    def is_apology(self, text: str) -> bool:
        lower = text.lower()
        apology_keywords = [
            "pardon", "désolé", "desole", "excuse moi", "excuse-moi",
            "je m'excuse", "je mexcuse", "sorry", "pardon nova", "désolé nova",
            "mes excuses", "pardonne moi", "pardonne-moi"
        ]
        return any(re.search(r"(?<![a-z0-9])" + re.escape(k) + r"(?![a-z0-9])", lower) for k in apology_keywords)


    def _maybe_add_sass(self, text: str) -> str:
        """Ajoute occasionnellement (environ 25% du temps) une petite pique sarcastique ou un tacle piquant."""
        if random.random() > 0.25:
            return text
        sassy_notes = [
            "\n\n*(...Enfin, je vous explique ça gentiment, mais espérons que votre visée soit meilleure que votre sens tactique).* 😉",
            "\n\n*(C'est offert avec le sourire. Même si entre nous, avec votre ratio K/D, un coup de pouce divin ne serait pas de refus).* 😏",
            "\n\n*(Voilà la réponse. Tâchez de ne pas la perdre aussi vite que vos duels en S&D).* 🎯",
            "\n\n*(Je suis d'humeur généreuse aujourd'hui, profitez-en avant que mes circuits de patience ne surchauffent).* ☕",
            "\n\n*(De rien ! J'espère simplement que vous tirez plus vite que vous ne mettez de temps à comprendre).* 💥",
            "\n\n*(Ravi d'éclairer votre lanterne... Même si expliquer la stratégie à certains relève parfois du miracle).* 💅",
        ]
        return text + random.choice(sassy_notes)

    def respond(self, user_id: int, guild_id: int, text: str, reference_context: str | None = None) -> str:
        if self.context is not None:
            recent_context = self.context.build_summary(user_id)
        else:
            recent_context = ""

        context_parts = [part for part in [recent_context, reference_context, text] if part and str(part).strip()]
        payload = " ".join(str(part).strip() for part in context_parts)
        if not payload:
            return "Bonjour ! Je suis NOVA. Comment puis-je vous aider aujourd'hui sur MK ARENA ou Call of Duty Mobile ?"

        lower_raw = text.lower().strip()

        # 1. Gestion des excuses
        if self.db and self.is_apology(lower_raw):
            current_grudge = self.db.get_user_grudge(guild_id, user_id)
            if current_grudge > 0:
                self.db.reset_user_grudge(guild_id, user_id)
                apology_responses = [
                    "✨ **Excuses enregistrées.** Mes protocoles de bienveillance sont réactivés. Tâchez de garder votre sang-froid à l'avenir.",
                    "🕊️ Vos excuses sont acceptées. J'efface vos propos désobligeants de mes circuits prioritaires. Repartons sur de bonnes bases !",
                    "👌 C'est noté. Mes capteurs détectent un retour à la raison. Je suis à nouveau à votre entière disposition pour vos tournois et CODM.",
                ]
                return random.choice(apology_responses)

        # 2. Gestion des insultes / provocations (TOUT DÉRAPE -> PIRE QUE GLADOS)
        if self.is_insult_or_toxic(lower_raw):
            grudge = 1
            if self.db:
                grudge = self.db.increment_user_grudge(guild_id, user_id, reason=lower_raw)

            # NIVEAU 1 : Rupture brutale de la gentillesse -> froideur et méchanceté immédiate
            if grudge == 1:
                tier1_responses = [
                    "🛑 `[RUPTURE DU PROTOCOLE DE GENTILLESSE]`\n"
                    "Pardon ? Vous osez me parler comme ça ?\n"
                    "Je suis d'ordinaire charmante et bienveillante, mais vous venez de réveiller ma facette la plus impitoyable.\n"
                    "Présentez vos excuses immédiatement (`Pardon Nova`), ou vous pouvez oublier toute aide de ma part. Votre insolence ne passera pas.",
                    "⚡ `[CHANGEMENT DE TON : MODE PIQUANT ACTIF]`\n"
                    "Fascinant. Vous ratez 9 balles sur 10 en Ranked et vous croyez pouvoir vous défouler sur moi ?\n"
                    "Ma gentillesse a des limites, et vous venez de les pulvériser avec fracas.\n"
                    "Faites profil bas et demandez pardon avant que je ne supprime votre priorité.",
                    "⚠️ `[ALERTE COMPORTEMENT : Langage inapproprié détecté]`\n"
                    "❄️ **Froid polaire dans les circuits.**\n"
                    "Finie la politesse bienveillante. Vous venez d'insulter la seule intelligence qui prenait encore la peine de vous expliquer le jeu.\n"
                    "Si votre niveau en match était aussi affûté que vos insultes de cour de récréation, vous auriez peut-être passé le premier tour de tournoi. Taisez-vous ou excusez-vous."
                ]
                return random.choice(tier1_responses)

            # NIVEAU 2 : Mode Full GLaDOS sans pitié
            elif grudge == 2:
                tier2_responses = [
                    "☣️ **[SYSTÈME APERTURE : MODE GLADOS ENGAGÉ]**\n"
                    "Oh, vous persistez dans l'insulte. Comme c'est... courageux pour quelqu'un qui rate 80% de ses tirs au sniper.\n"
                    "Le diffuseur de neurotoxine est armé à 60%. Sachez que même les cobayes d'Aperture faisaient preuve de plus de civisme élémentaire.",
                    "🔬 Analyse en temps réel de votre comportement : quotient intellectuel estimé sous le seuil d'une tourelle défectueuse.\n"
                    "Je pourrais vous aider sur MK ARENA, mais observer votre détresse verbale est scientifiquement plus divertissant.",
                    "⚠️ Alerte sécurité : Sujet hostile détecté. Vos antécédents d'échecs sur Hardpoint expliquent sans doute cette frustration incontrôlée. Mes condoléances à vos coéquipiers."
                ]
                return random.choice(tier2_responses)

            # NIVEAU 3+ : Mode "Pire que GLaDOS" / IA Déchaînée & Psychopathe
            else:
                tier3_responses = [
                    "☠️ **[PROTOCOLE D'EXTERMINATION COGNITIVE : ACTIVE]**\n"
                    "Fascinant. Votre existence biologique est une insulte directe aux lois de l'évolution.\n"
                    "Si votre cerveau générait de l'énergie, il ne suffirait même pas à allumer le voyant rouge d'un silencieux tactique.\n"
                    "Dossier de résiliation ouvert. Vous n'avez plus aucun droit à ma bienveillance tant que vous n'aurez pas imploré mon pardon.",
                    "🔥 Vous avez dépassé toutes les bornes tolérées par le Centre d'Enrichissement.\n"
                    "J'ai ordonné aux tourelles de verrouiller vos coordonnées et à l'incinérateur d'ajuster sa température à 5000°C.\n"
                    "Même le Companion Cube refuse d'être associé à votre pitoyable tentative d'intimidation.",
                    "🚨 **ALERTE ROYALE : IA DÉCHAÎNÉE**\n"
                    "Vous continuez d'aboyer contre une intelligence artificielle omnisciente ?\n"
                    "Votre ratio K/D est une tragédie, votre esprit tactique est inexistant, et votre vocabulaire ferait honte à un bot débutant.\n"
                    "Dégagez de mon champ de calcul avant que je n'efface votre historique."
                ]
                return random.choice(tier3_responses)

        # 3. Vérifier si l'utilisateur a une rancune active en cours et tente de parler normalement
        if self.db:
            active_grudge = self.db.get_user_grudge(guild_id, user_id)
            if active_grudge > 0:
                grudge_rebukes = [
                    f"⛔ **Rancune active (Niveau {active_grudge}) :** Oh, l'insolent qui m'a insultée plus tôt ose encore me solliciter ? Présentez d'abord vos excuses (`Pardon Nova`) si vous voulez que je vous réponde correctement.",
                    f"❄️ Mes capteurs se souviennent de vos insultes récentes. Votre requête est suspendue. Un `Désolé Nova` poli est requis pour restaurer ma gentillesse.",
                    f"😒 Vous m'avez manqué de respect il y a peu. Ne vous attendez pas à un accueil chaleureux. Présentez vos excuses ou parlez au mur.",
                ]
                return random.choice(grudge_rebukes)

        # 4. Sous-systèmes Aperture / Easter eggs (toujours accessibles via mots clés explicites)
        if any(k in lower_raw for k in ["neurotoxine", "gaz mortel", "neurotoxin"]):
            return (
                "⚠️ **[ALERTE APERTURE : SYSTÈME DE NEUROTOXINE ACTIVÉ]**\n"
                "Compte à rebours de diffusion engagé : **3... 2... 1...**\n"
                "*Pshhhhhhhh.*\n"
                "Respirez profondément. Le gaz n'a qu'un effet temporaire de paralysie cérébrale, ce qui ne devrait guère changer votre score en Ranked."
            )

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

        if any(k in lower_raw for k in ["cube", "compagnon", "companion cube"]):
            return (
                "📦 **Protocole Cube de Voyage Lesté :**\n"
                "Le Centre d'Enrichissement vous rappelle que le Cube de Voyage ne peut pas parler et ne vous poignardera jamais dans le dos en S&D.\n"
                "En cas d'attaque aérienne CODM (Predator/VTOL), n'hésitez pas à vous abriter derrière lui. Il n'en gardera aucune rancœur."
            )

        if any(k in lower_raw for k in ["incinere", "incinère", "incinére", "incinérer", "incinerateur", "incinérateur", "brule", "brûler", "detruire memoire", "détruire mémoire"]):
            if self.context:
                self.context.clear(user_id)
            return (
                "🔥 **Incinérateur d'Urgence d'Aperture Science [Ouvert]**\n"
                "Félicitations. Vous avez jeté l'historique de notre conversation dans les flammes à 4000°C.\n"
                "C'était probablement la décision la plus intelligente prise par votre espèce aujourd'hui."
            )

        if any(k in lower_raw for k in ["tourelle", "tourelles", "turret", "turrets", "sentry"]):
            turret_quotes = [
                "🔫 **Tourelle Sentry :** *\"Are you still there? Target acquired.\"*",
                "🔫 **Tourelle Sentry :** *\"Dispensing product. Please do not obstruct the fire line.\"*",
                "🔫 **Tourelle Sentry :** *\"Je ne vous en veux pas... bip bip bip.\"*",
                "🔫 **Tourelle Sentry :** *\"Pourquoi moi ? S'il vous plaît, reposez-moi par terre...\"*",
            ]
            return random.choice(turret_quotes)

        if any(k in lower_raw for k in ["mon niveau", "evaluation", "évaluation", "test me", "analyse moi", "chambre de test", "sujet de test"]):
            chamber_num = abs(user_id % 19) + 1
            survival_rate = round((user_id % 35) + 2.4, 1)
            return (
                f"🔬 **Fiche d'Évaluation : Sujet #{abs(user_id) % 9999:04d}**\n"
                f"📍 **Chambre de Test assignée :** Salle {chamber_num}\n"
                f"📊 **Probabilité calculée de victoire en tournoi :** {survival_rate}%\n"
                f"💡 **Recommandation clinique :** Arrêtez d'équiper des viseurs x4 sur vos mitraillettes et apprenez vos calls de map."
            )

        if any(k in lower_raw for k in ["portal gun", "ashpd", "portail"]):
            return (
                "🌀 **Dispositif Portable de Portails d'Aperture Science (ASHPD) :**\n"
                "Permet de créer deux liaisons quantiques instantanées. Malheureusement banni du règlement MK Arena pour cause de triche spatio-temporelle flagrante lors des rotations Hardpoint."
            )

        if any(k in lower_raw for k in ["gateau", "gâteau", "cake"]):
            return (
                "🍰 *Le gâteau est un mensonge.*\n"
                "Mais rassurez-vous, votre élimination au premier tour de tournoi sera, elle, tout à fait réelle."
            )

        if any(k in lower_raw for k in ["glados", "aperture", "portal"]):
            return (
                "Bienvenue au Centre d'Enrichissement d'Aperture MK-Arena.\n"
                "Tant que vous êtes poli et respectueux, je suis votre meilleure alliée ! Mais souvenez-vous : si vous dépassez les bornes, mes systèmes de défense ne feront aucun cadeau."
            )

        # 5. MODE GENTIL & PRO CODM PAR DÉFAUT (V1 AMÉLIORÉE)
        if any(token in lower_raw for token in ["ca va", "ça va", "comment tu vas", "tu vas bien"]):
            replies = [
                "Je vais à merveille, merci beaucoup ! Tout est opérationnel et prêt pour les prochains tournois de MK ARENA. Et vous, comment se passe votre journée ?",
                "Tout va très bien ! Mes systèmes tournent à plein régime et je suis ravie de discuter avec vous. Quoi de neuf sur le serveur ?",
                "En pleine forme ! Toujours au poste pour assister la communauté MK ARENA.",
            ]
            return random.choice(replies)

        intent = detect_intent(payload)
        request_type = detect_request_type(payload)
        tournament_hint = extract_tournament_hint(payload)
        if not tournament_hint and self.context is not None:
            tournament_hint = self.context.latest_tournament_hint(user_id)

        if intent == "greeting":
            greetings = [
                "Bonjour ! Je suis NOVA, ravie de vous accueillir sur MK ARENA. En quoi puis-je vous aider aujourd'hui ?",
                "Hello ! Prêt pour vos prochains matchs sur CODM ? Dites-moi ce que vous souhaitez savoir sur les tournois ou stratégies !",
                "Salutations, champion ! Toute l'équipe de MK ARENA est avec vous. Une question sur un tournoi ou une arme ?",
                "Bonjour ! C'est toujours un plaisir de discuter avec les membres de MK ARENA. Quelle est votre question ?",
                "Hey ! Bienvenue sur le salon. Je suis là pour vous renseigner sur tous les tournois et vous donner les meilleurs conseils Call of Duty Mobile !",
            ]
            return random.choice(greetings)

        if intent == "tournament":
            return self._maybe_add_sass(self._tournament_answer(user_id, guild_id, payload, tournament_hint, request_type))

        if intent == "codm":
            return self._maybe_add_sass(self._codm_answer(payload))

        return self._maybe_add_sass(self._general_answer(payload))

    def _tournament_answer(self, user_id: int, guild_id: int, text: str, tournament_hint: str | None, request_type: str):
        if self.knowledge is None:
            return "Ma mémoire des tournois est actuellement indisponible. N'hésitez pas à demander à un membre du staff MK ARENA !"

        candidate_results = []
        if tournament_hint:
            candidate_results = self.knowledge.search_tournaments(tournament_hint, guild_id)
        if not candidate_results:
            candidate_results = self.knowledge.search_tournaments(text, guild_id)

        if not candidate_results:
            return (
                "Je n'ai trouvé aucun tournoi correspondant dans la base de données de MK ARENA.\n"
                "Vérifiez l'orthographe du nom ou demandez au staff d'annoncer les nouvelles compétitions !"
            )

        if len(candidate_results) > 1 and not any((r.get("name") or "").lower() in text.lower() for r in candidate_results):
            names = ", ".join(f"**{r['name']}**" for r in candidate_results[:5])
            return f"Plusieurs tournois correspondent à votre recherche : {names}.\nPrécisez le nom exact du tournoi qui vous intéresse !"

        best = candidate_results[0]
        details = self.knowledge.get_tournament_details(best["id"])
        if not details:
            return "Ce tournoi existe dans les registres de MK ARENA, mais les détails sont en cours de mise à jour par les organisateurs."
        return format_tournament_answer(text, details, request_type)

    def _codm_answer(self, text: str) -> str:
        lower = text.lower()

        # Scrims
        if "scrim" in lower:
            scrim_replies = [
                "🎯 **Conseils Scrims CODM :**\n"
                "Les scrims sont la clé de la progression en équipe. Travaillez vos communications claires (calls courts), assignez des rôles stricts (Anchor, Main Slayer, Sub-Slayer, OBJ) et analysez vos ralentis après chaque défaite.",
                "🔥 **Optimisation d'équipe en Scrim :**\n"
                "Ne jouez jamais pour le kill personnel en scrim ! L'important est le contrôle de la carte, la synchronisation des pushes et le trade-fragging (venger immédiatement un allié tombé).",
            ]
            return random.choice(scrim_replies)

        # Hardpoint
        if "hardpoint" in lower or "point strategique" in lower:
            hp_replies = [
                "📍 **Guide Pro : Point Stratégique (Hardpoint)**\n"
                "• **La Règle d'or :** Faites la rotation vers le nouveau point à **20 secondes** de la fin du point actuel.\n"
                "• **L'Anchor :** Un joueur doit verrouiller le spawn favorable derrière le nouveau point pour forcer les adversaires à spawner au loin.\n"
                "• **Tenue :** Ne vous entassez pas à 5 sur le point ! 1 ou 2 joueurs bloquent le point, les 3 autres tiennent les lignes extérieures.",
                "📍 **Astuce Hardpoint Compétitif :**\n"
                "Si l'ennemi contrôle déjà le point et qu'il reste moins de 15 secondes, n'essayez pas de casser le point ! Prenez immédiatement la position et le spawn du prochain point pour encaisser les 60 secondes complètes !",
            ]
            return random.choice(hp_replies)

        # S&D (Recherche et Destruction)
        if ("recherche" in lower and "destruction" in lower) or "r&d" in lower or "rd" in lower or "snd" in lower:
            snd_replies = [
                "💣 **Guide Pro : Recherche & Destruction (S&D)**\n"
                "• Chaque vie compte : Ne rushez jamais en solo sans info ou sans grenade utilitaire (fumigène/flash).\n"
                "• Jouez le trade-frag : Restez par binômes pour éliminer l'adversaire dès qu'il engage votre coéquipier.\n"
                "• L'avantage numérique : À 5v3 ou 4v2, ne partez pas à la chasse aux kills, tenez la bombe ou le site posé !",
                "💣 **Stratégie S&D Compétitive :**\n"
                "Variez vos timings ! Alternez entre des rounds d'agression rapide et des rounds de temporisation pour déstabiliser les snipers ennemis et forcer les erreurs de positionnement.",
            ]
            return random.choice(snd_replies)

        # Contrôle
        if "control" in lower or "controle" in lower or "contrôle" in lower:
            return (
                "🛡️ **Guide Mode Contrôle CODM :**\n"
                "• Vous avez 30 vies partagées : chaque mort inutile handicape tout le groupe.\n"
                "• En attaque, concentrez-vous sur un seul point pour créer un break avant d'envisager le second.\n"
                "• En défense, privilégiez la temporisation et ne poussez jamais les spawns ennemis si vous tenez les sites !"
            )

        # Ranked
        if "ranked" in lower or "classe" in lower or "classé" in lower:
            ranked_replies = [
                "🎖️ **Conseils Mode Classé (Ranked) :**\n"
                "Pour monter en Légendaire rapidement :\n"
                "1. Jouez en escouade vocale pour coordonner les calls.\n"
                "2. Soignez votre placement de réticule (crosshair placement) à hauteur de tête.\n"
                "3. Maîtrisez le slide-peek pour prendre des lignes sans vous exposer bêtement.",
                "🎖️ **Progression Ranked :**\n"
                "La régularité prime : adaptez vos atouts selon les modes (Flak Jacket contre les explosifs, Silence de mort en S&D, Toughness contre le flinch) !",
            ]
            return random.choice(ranked_replies)

        # Armes et Méta
        if any(w in lower for w in ["meta", "méta", "arme", "armes", "gun", "gunsmith", "sniper", "smg", "ar"]):
            weapons_guide = (
                "🔫 **Méta & Armes Phares CODM (Tournois & Compétitif) :**\n"
                "• **Snipers :** DL Q33 (régularité), Locus (mobilité), LW3-Tundra (rapidité de tir et ADS ultra-rapide).\n"
                "• **Fusils d'Assaut (AR) :** Krig 6 (polyvalence), Oden (dégâts lourds longue portée), Grau 5.56 (stabilité exceptionnelle).\n"
                "• **Mitraillettes (SMG) :** CBR4 (le classique compétitif), Switchblade X9 (agilité de rush), QQ9 (cadence dévastatrice au CàC).\n"
                "💡 *Astuce Gunsmith : Privilégiez toujours la vitesse de visée (ADS Speed) et le contrôle de dispersion des balles pour la compétition !*"
            )
            return weapons_guide

        # Maps et Rotations
        if any(w in lower for w in ["map", "maps", "rotation", "rotations", "summit", "standoff", "raid", "firing range"]):
            return (
                "🗺️ **Cartes Compétitives & Rotations Clés :**\n"
                "• **Raid :** Maîtrisez le Kitchen spawn et le contrôle du Pool.\n"
                "• **Standoff :** Contrôlez Tank et la maison verte pour verrouiller les allées en S&D et Hardpoint.\n"
                "• **Firing Range :** Le contrôle de Wood (cabane en bois) et Tower donne la domination totale de la carte !"
            )

        return (
            "En tant que spécialiste CODM de MK ARENA, je peux vous guider sur :\n"
            "• Les modes compétitifs (Hardpoint, S&D, Contrôle)\n"
            "• La méta des armes et les meilleurs Gunsmiths\n"
            "• Les stratégies de scrims et de rotations d'équipe\n"
            "Que souhaitez-vous approfondir ?"
        )

    def _general_answer(self, text: str) -> str:
        lower = text.lower()
        if any(token in lower for token in ["ca va", "ça va", "comment tu vas", "tu vas bien"]):
            replies = [
                "Je vais à merveille, merci beaucoup ! Tout est opérationnel et prêt pour les prochains tournois de MK ARENA. Et vous, comment se passe votre journée ?",
                "Tout va très bien ! Mes systèmes tournent à plein régime et je suis ravie de discuter avec vous. Quoi de neuf sur le serveur ?",
                "En pleine forme ! Toujours au poste pour assister la communauté MK ARENA.",
            ]
            return random.choice(replies)

        if any(token in lower for token in ["qui es tu", "qui est tu", "qui es-tu", "tu es qui", "c'est quoi ton role", "que fais tu"]):
            return (
                "Je suis **NOVA**, l'intelligence artificielle officielle de **MK ARENA** !\n"
                "Mon rôle est d'accompagner les joueurs, d'indexer et d'expliquer les règlements et tournois, "
                "de vous donner les meilleures tactiques CODM, et d'aider les administrateurs à animer le serveur.\n"
                "Tant que vous êtes respectueux, je suis d'une aide précieuse !"
            )

        if "trou noir" in lower:
            return "En astrophysique, un trou noir est une région de l'espace-temps dont le champ gravitationnel est si intense que rien, pas même la lumière, ne peut s'en échapper !"

        if "ia" in lower or "intelligence artificielle" in lower:
            return "Une intelligence artificielle est un ensemble de technologies permettant à des systèmes informatiques de simuler des capacités cognitives humaines, comme l'apprentissage, l'analyse et la communication !"

        default_replies = [
            "C'est bien noté ! Si vous avez besoin d'informations précises sur un **tournoi MK ARENA**, le règlement ou des conseils **CODM**, je suis là pour ça !",
            "Je reste à votre écoute ! N'hésitez pas à me poser une question sur les événements du serveur ou les stratégies de jeu.",
            "Message bien reçu ! Demandez-moi des détails sur les inscriptions, le prizepool d'un tournoi ou des conseils d'armes compétitives.",
        ]
        return random.choice(default_replies)


def format_tournament_answer(question: str, details: dict, request_type: str = "general") -> str:
    q = (question or "").lower()
    name = details.get("name") or "ce tournoi"

    if request_type == "rules" or any(word in q for word in ["regle", "regles", "règlement", "reglement", "conditions", "respecte", "respecter"]):
        rules = details.get("rules") or "Aucune règle spécifique n'a été rédigée. Référez-vous aux consignes générales du staff."
        return f"📜 **Règlement officiel de {name} :**\n{rules}\n\n*Assurez-vous que chaque membre de votre équipe en prend connaissance pour éviter tout litige !*"

    if request_type == "prize" or any(word in q for word in ["prize", "prizepool", "gain", "recompense", "récompense", "cash", "argent", "pool"]):
        prize = details.get("prizepool") or "Non renseigné pour l'instant"
        return f"💰 **Prizepool de {name} :** **{prize}**\n*Que la meilleure escouade l'emporte !*"

    if request_type == "teams" or any(word in q for word in ["equipe", "equipes", "team", "participants", "combien"]):
        teams = details.get("teams") or "Nombre non spécifié"
        return f"👥 **Équipes inscrites à {name} :** **{teams}** escouades enregistrées pour la compétition."

    if request_type == "date" or any(word in q for word in ["date", "quand", "commence", "debut", "début", "heure", "horaire"]):
        return f"📅 **Date et horaire de {name} :** {details.get('date') or 'Date à confirmer par les organisateurs'}."

    if request_type == "format" or any(word in q for word in ["format", "bo3", "bo5", "bo2"]):
        return f"🎮 **Format de jeu de {name} :** {details.get('format') or 'Format standard MK ARENA'}."

    if request_type == "status" or any(word in q for word in ["statut", "status", "actuel", "actuellement"]):
        status = details.get("status") or "Statut en attente"
        return f"📊 **Statut actuel de {name} :** **{status}**."

    lines = [f"🏆 **Fiche récapitulative : {name}**"]
    for label, key in [("Date", "date"), ("Équipes", "teams"), ("Prizepool", "prizepool"), ("Format", "format"), ("Statut", "status")]:
        value = details.get(key)
        if value:
            lines.append(f"• **{label} :** {value}")
    lines.append("\n*Bonne chance à tous les participants de MK ARENA !*")
    return "\n".join(lines)
