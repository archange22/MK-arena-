from __future__ import annotations


def build_reference_context(reference_text: str | None):
    if not reference_text:
        return None
    cleaned = " ".join(str(reference_text).strip().split())
    return cleaned[:500] if cleaned else None


def format_nova_status(version: str, db, tournament_scanner, knowledge_count: int) -> str:
    lines = [
        "🔬 **NOVA / Protocole GLaDOS v2.0 - Statut opérationnel**",
        "> *\"Oh, c est encore vous. Comme c est... fascinant.\"*",
        "",
        f"⚙️ **Version :** {version} (Matrice Aperture-Arena)",
        f"💾 **Mémoire SQLite :** Optimale (0 erreur matérielle, contrairement à vos réflexes)",
        f"🏆 **Protocoles de test (Tournois) indexés :** {db.count_tournaments()}",
        f"🧠 **Données cognitives enregistrées :** {knowledge_count}",
    ]
    if tournament_scanner is None:
        lines.append("📡 **Scanner tournois :** Inactif (vous m épargnez l analyse de vos défaites)")
    else:
        lines.append("📡 **Scanner tournois :** Actif (surveillance des sujets de test en cours)")
    lines.append("
🍰 *Rappel de sécurité : Le gâteau n est toujours pas garanti.*")
    return "\n".join(lines)
