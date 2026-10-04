import re
import time
from collections import defaultdict

class AutoModManager:
    def __init__(self):
        self.user_message_times = defaultdict(list)
        self.invite_pattern = re.compile(r"(discord\.(gg|io|me|li)|discordapp\.com/invite|discord\.com/invite)/[a-zA-Z0-9]+", re.IGNORECASE)
        self.url_pattern = re.compile(r"https?://[^\s]+", re.IGNORECASE)

    def check_message(self, user_id: int, content: str, settings: dict) -> tuple[bool, str]:
        """
        Vérifie un message selon les réglages automod du serveur.
        Renvoie (is_violation, reason).
        """
        now = time.time()
        
        # 1. Anti-Spam
        if settings.get("automod_spam"):
            times = self.user_message_times[user_id]
            # Conserver les timestamps des 4 dernières secondes
            times = [t for t in times if now - t < 4.0]
            times.append(now)
            self.user_message_times[user_id] = times
            if len(times) >= 5:
                return True, "Anti-Spam : Envoi de messages trop rapide (flood)"

        # 2. Anti-Invites Discord
        if settings.get("automod_invites"):
            if self.invite_pattern.search(content):
                return True, "Anti-Pub : Liens d'invitation Discord interdits"

        # 3. Anti-Liens globaux
        if settings.get("automod_links"):
            if self.url_pattern.search(content):
                return True, "Anti-Liens : Liens externes non autorisés"

        # 4. Anti-Majuscules
        if settings.get("automod_caps") and len(content) >= 10:
            letters = [c for c in content if c.isalpha()]
            if letters:
                caps = [c for c in letters if c.isupper()]
                ratio = len(caps) / len(letters)
                if ratio > 0.70:
                    return True, "Anti-Majuscules : Abus de lettres capitales"

        # 5. Mots interdits / Blacklist
        blacklist = settings.get("automod_blacklist", "")
        if blacklist:
            words = [w.strip().lower() for w in blacklist.split(",") if w.strip()]
            content_lower = content.lower()
            for word in words:
                if re.search(r"\b" + re.escape(word) + r"\b", content_lower):
                    return True, f"Mot prohibé détecté : '{word}'"

        return False, ""
