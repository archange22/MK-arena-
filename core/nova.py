"""NOVA Core Orchestrator (v5 Architecture)"""
from typing import Dict, Any, Optional
from core.lifecycle import LifecycleManager
from core.config import NovaConfig

class NovaCore:
    """The central brain orchestrating AI, Memory, Tools, Agent, and Interfaces"""
    def __init__(self, db=None, ai_engine=None):
        self.config = NovaConfig()
        self.lifecycle = LifecycleManager()
        self.db = db
        self.ai_engine = ai_engine
        
        # Subsystem references
        self.memory = None
        self.tools = None
        self.agent = None
        self.personality = None
        self.security = None
        self.git = None
        self.self_improvement = None
        
        self.lifecycle.set_status("READY")

    def process_message(self, user_id: int, guild_id: int, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Central pipeline: Input -> Context -> Memory -> AI Engine -> Personality -> Response"""
        if self.ai_engine and hasattr(self.ai_engine, "respond"):
            return self.ai_engine.respond(user_id, guild_id, text)
        return f"[NOVA Core v{self.config.VERSION}] Message received: {text}"

    def status(self) -> Dict[str, Any]:
        return {
            "version": self.config.VERSION,
            "codename": self.config.CODENAME,
            "health": self.lifecycle.health(),
            "backend": self.config.AI_MODEL_BACKEND
        }
