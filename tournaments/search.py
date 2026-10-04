from ai.intent import normalize_text, TOURNAMENT_ALIASES


def find_tournament(db, query: str, guild_id: int):
    cleaned = normalize_text(query)
    if not cleaned:
        # Renvoie le tournoi le plus récent ou actif
        rows = db.query(
            "SELECT * FROM tournaments WHERE guild_id = ? ORDER BY id DESC LIMIT 1",
            (guild_id,),
        )
        return dict(rows[0]) if rows else None

    # Résolution alias
    target = TOURNAMENT_ALIASES.get(cleaned, cleaned)

    rows = db.query(
        "SELECT * FROM tournaments WHERE guild_id = ? AND (LOWER(name) LIKE ? OR LOWER(name) LIKE ?) ORDER BY id DESC LIMIT 1",
        (guild_id, f"%{target}%", f"%{cleaned}%"),
    )
    if rows:
        return dict(rows[0])

    # Fallback recherche globale
    rows = db.query(
        "SELECT * FROM tournaments WHERE guild_id = ? ORDER BY id DESC LIMIT 1",
        (guild_id,),
    )
    return dict(rows[0]) if rows else None
