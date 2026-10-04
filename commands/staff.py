from discord_bot.permissions import can_manage_nova


class StaffCommands:
    def __init__(self, knowledge, indexer):
        self.knowledge = knowledge
        self.indexer = indexer

    def handle_admin_action(self, member, text: str, guild_id: int) -> str:
        if not can_manage_nova(member):
            return "Tu n'as pas les permissions nécessaires pour exécuter cette action administrative."

        cleaned = text.strip()
        if cleaned.lower().startswith(("nova ", "nova:")):
            cleaned = cleaned[4:].lstrip(": ").strip()

        # Apprentissage explicite
        if any(k in cleaned.lower() for k in ["retiens", "enregistre", "voici les regles", "regle"]) :
            return self.knowledge.learn(cleaned, source=f"staff:{member.id}", guild_id=guild_id)

        return f"Compris. Instruction administrative enregistrée : {cleaned}"
