"""Semantic and TF-IDF / keyword similarity matcher for memory"""
import math
import re
from typing import List, Dict, Tuple, Any

class SemanticSearch:
    @staticmethod
    def tokenize(text: str) -> List[str]:
        return re.findall(r'\w+', text.lower())

    @classmethod
    def similarity(cls, text_a: str, text_b: str) -> float:
        tokens_a = set(cls.tokenize(text_a))
        tokens_b = set(cls.tokenize(text_b))
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = tokens_a.intersection(tokens_b)
        union = tokens_a.union(tokens_b)
        return len(intersection) / len(union)

    @classmethod
    def rank(cls, query: str, documents: List[Dict[str, Any]], key: str = "content") -> List[Tuple[float, Dict[str, Any]]]:
        ranked = []
        for doc in documents:
            score = cls.similarity(query, doc.get(key, ""))
            if score > 0:
                ranked.append((score, doc))
        return sorted(ranked, key=lambda x: x[0], reverse=True)
