"""Structured output validator and schema enforcement"""
import json
from typing import Dict, Any, Optional

class StructuredOutputParser:
    @staticmethod
    def parse_json(raw_text: str) -> Optional[Dict[str, Any]]:
        raw_text = raw_text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        try:
            return json.loads(raw_text)
        except Exception:
            return None

    @staticmethod
    def enforce_schema(data: dict, required_keys: list) -> bool:
        return all(k in data for k in required_keys)
