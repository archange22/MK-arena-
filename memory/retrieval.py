"""Multi-tier Memory Retriever"""
from typing import List, Dict, Any
from memory.semantic import SemanticSearch

class MemoryRetriever:
    def __init__(self, db, knowledge=None):
        self.db = db
        self.knowledge = knowledge

    def retrieve(self, query: str, guild_id: int, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        results = []
        if self.knowledge:
            ranked = SemanticSearch.rank(query, self.knowledge.get("facts", []), key="text")
            results.extend([r[1] for r in ranked[:limit]])
        return results
