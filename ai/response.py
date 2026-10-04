from __future__ import annotations


def build_reference_context(reference_text: str | None):
    if not reference_text:
        return None
    cleaned = " ".join(str(reference_text).strip().split())
    return cleaned[:500] if cleaned else None


def format_nova_status(version: str, db, tournament_scanner, knowledge_count: int) -> str:
    lines = [
        "🟢 NOVA en ligne",
        f"Version : {version}",
        f"Base SQLite : OK",
        f"Tournois indexés : {db.count_tournaments()}",
        f"Connaissances enregistrées : {knowledge_count}",
    ]
    if tournament_scanner is None:
        lines.append("Scanner tournois : indisponible")
    else:
        lines.append("Scanner tournois : prêt")
    return "\n".join(lines)
