from __future__ import annotations


def build_reference_context(reference_text: str | None):
    if not reference_text:
        return None
    cleaned = " ".join(str(reference_text).strip().split())
    return cleaned[:500] if cleaned else None
