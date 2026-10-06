import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
PORT = int(os.getenv("PORT", "10000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
PREFIX = os.getenv("PREFIX", "!").strip() or "!"
