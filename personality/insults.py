"""Insult detection, grudge management, and apology handling"""
import re

class InsultDetector:
    PATTERNS = [
        r"\b(tg|ferme\s+ta\s+gueule|conne|salope|idiote|inutile|nul|merde|fdp)\b"
    ]
    APOLOGY_PATTERNS = [
        r"\b(pardon|désolé|desole|excuse|m'excuse)\b"
    ]

    @classmethod
    def is_insult(cls, text: str) -> bool:
        low = text.lower()
        return any(re.search(p, low) for p in cls.PATTERNS)

    @classmethod
    def is_apology(cls, text: str) -> bool:
        low = text.lower()
        return any(re.search(p, low) for p in cls.APOLOGY_PATTERNS)
