"""Secret scanner: prevents leaks in commits, logs or memory"""
import re

class SecretScanner:
    PATTERNS = [
        r"(?i)discord[_-]?token[\s:=]+([a-zA-Z0-9_\.\-]{24,})",
        r"(?i)ghp_[a-zA-Z0-9]{36}",
        r"(?i)api[_-]?key[\s:=]+['\"][a-zA-Z0-9_\-]{20,}['\"]",
        r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{25,}"
    ]

    @classmethod
    def contains_secret(cls, text: str) -> bool:
        return any(re.search(p, text) for p in cls.PATTERNS)

    @classmethod
    def sanitize(cls, text: str) -> str:
        sanitized = text
        for p in cls.PATTERNS:
            sanitized = re.sub(p, "[REDACTED SECRET]", sanitized)
        return sanitized
