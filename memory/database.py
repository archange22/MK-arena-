from __future__ import annotations

from datetime import datetime, timezone


def format_nova_status(version: str, db, scanner, knowledge_count: int) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC")
    scanner_state = "OK" if scanner else "Non initialisé"
    return (
        f"🟢 NOVA v{version}\n"
        f"Heure : {timestamp}\n"
        f"Mémoire SQLite : OK\n"
        f"Tournois indexés : {db.count_tournaments()}\n"
        f"Connaissances enregistrées : {knowledge_count}\n"
        f"Scanner : {scanner_state}"
    )
