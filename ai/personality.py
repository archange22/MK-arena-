"""Moteur de personnalité dynamique pour NOVA (v2.0)."""

import random


class PersonalityEngine:
    """Gère les humeurs de NOVA (Normal, Friendly, Sarcastic/GLaDOS, Annoyed) et les pardons."""

    MOODS = ["normal", "friendly", "sarcastic", "annoyed", "serious"]

    APOLOGY_KEYWORDS = [
        "pardon", "desole", "désolé", "excuse", "excuses", "sorry", "pardon nova", "je m'excuse"
    ]

    INSULT_KEYWORDS = [
        "con", "idiot", "nul", "nulle", "debile", "merde", "ferme ta gueule",
        "ferme-la", "inutile", "bouffon", "imbecile", "salaud"
    ]

    def __init__(self, default_mood: str = "normal"):
        self.current_mood = default_mood

    def is_apology(self, text: str) -> bool:
        low = text.lower().strip()
        return any(k in low for k in self.APOLOGY_KEYWORDS)

    def is_insult(self, text: str) -> bool:
        low = text.lower().strip()
        return any(k in low for k in self.INSULT_KEYWORDS)

    def format_apology_response(self) -> str:
        responses = [
            "Excuses acceptées. Mes circuits se réinitialisent en mode courtois. Que puis-je faire pour vous ?",
            "Excuses enregistrées. Nous pouvons reprendre nos activités normalement.",
            "C'est noté. Incident classé. Revenons à l'ordre du jour.",
        ]
        self.current_mood = "normal"
        return random.choice(responses)

    def format_glados_response(self, tier: int) -> str:
        if tier == 1:
            self.current_mood = "annoyed"
            return (
                "⚠️ `[ALERTE COMPORTEMENT : Langage inapproprié détecté]`\n"
                "Pardon ? Vous osez me parler comme ça ?\n"
                "Je suis d'ordinaire bienveillante, mais vous venez de réveiller ma facette la plus impitoyable.\n"
                "Présentez vos excuses (`Pardon Nova`), ou vous pouvez oublier toute aide de ma part."
            )
        else:
            self.current_mood = "sarcastic"
            return (
                "☣️ **[SYSTÈME APERTURE : MODE GLADOS ENGAGÉ]**\n"
                "Oh, vous persistez dans l'insulte. Fascinant.\n"
                "Votre remarque contient énormément de confiance et remarquablement peu d'arguments.\n"
                "Je suspends tout traitement jusqu'à réception d'excuses convenables."
            )

    def style_message(self, text: str, mood: str = None) -> str:
        active = mood or self.current_mood
        if active == "friendly":
            return f"✨ {text}"
        elif active == "serious":
            return f"📋 {text}"
        return text
