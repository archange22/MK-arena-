"""Discord mention and name invocation parser"""
import re

class MentionParser:
    NAME_REGEX = re.compile(r"^\s*nova[\s,!:?]+", re.IGNORECASE)

    @classmethod
    def is_invoked(cls, content: str, bot_user_id: int = None, mentioned_ids: list = None) -> bool:
        if bot_user_id and mentioned_ids and bot_user_id in mentioned_ids:
            return True
        return bool(cls.NAME_REGEX.search(content) or content.lower().strip() == "nova")

    @classmethod
    def strip_invocation(cls, content: str) -> str:
        return cls.NAME_REGEX.sub("", content).strip()
