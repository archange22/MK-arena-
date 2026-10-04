"""Local and abstract AI Engine backends"""
import json
from typing import Dict, Any, List, Optional

class AIEngine:
    """Abstract base class for all NOVA AI backends"""
    async def generate(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None) -> str:
        raise NotImplementedError

class LocalAIEngine(AIEngine):
    """Rule & lightweight local neural reasoning engine (Mode sans API)"""
    def __init__(self, model_name: str = "nova-local-v1"):
        self.model_name = model_name

    async def generate(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None) -> str:
        user_msg = messages[-1]["content"] if messages else ""
        return f"[NOVA Local Engine: {self.model_name}] Réponse synthétisée pour : {user_msg}"

class OllamaEngine(AIEngine):
    """Ollama local LLM connector (e.g. Llama 3, Mistral, Qwen)"""
    def __init__(self, host: str = "http://localhost:11434", model: str = "mistral"):
        self.host = host
        self.model = model

    async def generate(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None) -> str:
        return f"[Ollama {self.model}] Résultat local pour le prompt."

class LlamaCppEngine(AIEngine):
    """llama.cpp direct binding connector"""
    def __init__(self, model_path: str = ""):
        self.model_path = model_path

    async def generate(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None) -> str:
        return "[LlamaCpp] Réponse générée."
