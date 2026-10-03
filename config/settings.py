import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass(frozen=True)
class Settings:
    discord_token: str
    database_path: str
    tournament_category_id: int | None
    nova_log_channel_id: int | None
    context_ttl_minutes: int

def _optional_int(name: str):
    value = os.getenv(name, "").strip()
    if not value or value == "0":
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} doit être un entier Discord valide.") from exc

def load_settings() -> Settings:
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise RuntimeError("DISCORD_TOKEN est manquant dans .env")
    return Settings(
        discord_token=token,
        database_path=os.getenv("DATABASE_PATH", "nova.db"),
        tournament_category_id=_optional_int("TOURNAMENT_CATEGORY_ID"),
        nova_log_channel_id=_optional_int("NOVA_LOG_CHANNEL_ID"),
        context_ttl_minutes=int(os.getenv("NOVA_CONTEXT_TTL_MINUTES", "30")),
    )
