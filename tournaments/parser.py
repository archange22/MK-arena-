import re


def extract_tournament_fields(text: str) -> dict:
    if not text:
        return {}

    details = {}
    cleaned = text.strip()

    # Format (BO3, BO5, etc.)
    fmt = re.search(r"(BO[1357])", cleaned, re.IGNORECASE)
    if fmt:
        details["format"] = fmt.group(1).upper()

    # Équipes
    teams = re.search(r"(?:equipes?|teams?)\s*(?:actuellement)?\s*(?:sont|=|est|:)?\s*(\d+)", cleaned, re.IGNORECASE)
    if teams:
        details["teams"] = teams.group(1)

    # Prizepool / Cashprize
    prizepool = re.search(r"(?:prizepool|prize|cashprize|recompense)\s*(?:est|de|=|:)?\s*([0-9]+(?:\s*€|\s*euros?|\s*\$|\s*usd)?)", cleaned, re.IGNORECASE)
    if prizepool:
        details["prizepool"] = prizepool.group(1).strip()

    # Date
    date = re.search(r"(?:date|le|debut|commence le)\s*(?:est|:)?\s*([0-9]{1,2}\s+[a-zà-ÿ]+\s*(?:[0-9]{4})?|[0-9]{1,2}/[0-9]{1,2}(?:/[0-9]{2,4})?)", cleaned, re.IGNORECASE)
    if date:
        details["date"] = date.group(1).strip()

    # Règles
    if re.search(r"(?:regles?|reglement|conditions?)", cleaned, re.IGNORECASE):
        details["rules"] = cleaned

    return details
