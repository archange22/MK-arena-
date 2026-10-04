"""Discord message sanitization and rate-limiting"""
class MessageSanitizer:
    @staticmethod
    def clean(content: str) -> str:
        # Strip excessive mentions, formatting attacks
        return content.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere").strip()
