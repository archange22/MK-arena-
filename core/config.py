"""NOVA Core Configuration"""
import os

class NovaConfig:
    VERSION = "5.0.0-alpha"
    CODENAME = "NOVA Autonomous Coding Agent & Personal AI"
    DEFAULT_MOOD = "NORMAL"
    MAX_REPAIR_ATTEMPTS = 5
    SANDBOX_TIMEOUT = 15
    AUDIT_ENABLED = True
    DB_PATH = os.getenv("NOVA_DB_PATH", "nova.db")
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8000"))
    AI_MODEL_BACKEND = os.getenv("AI_MODEL_BACKEND", "local") # local | ollama | llamacpp
