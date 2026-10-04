"""Rich Discord Embed builders for NOVA"""
class EmbedBuilder:
    @staticmethod
    def make_task_embed(task_id: str, title: str, status: str, steps: list) -> dict:
        return {
            "title": f"🛠️ Mission {task_id} : {title}",
            "color": 0x3498db if status == "SUCCESS" else 0xe74c3c,
            "fields": [
                {"name": "Statut", "value": status, "inline": True},
                {"name": "Étapes", "value": "\n".join(f"- {s}" for s in steps) or "Aucune", "inline": False}
            ]
        }
