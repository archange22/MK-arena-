import json

class PollSystem:
    def __init__(self, db):
        self.db = db

    def create_poll(self, guild_id: int, question: str, options: list[str]) -> int:
        opts_data = [{"id": i, "text": opt, "votes": []} for i, opt in enumerate(options)]
        cur = self.db.execute(
            """INSERT INTO polls (guild_id, question, options_json, status)
               VALUES (?, ?, ?, 'active')""",
            (guild_id, question, json.dumps(opts_data))
        )
        return cur

    def vote(self, poll_id: int, user_id: int, option_idx: int) -> tuple[bool, str]:
        rows = self.db.query("SELECT * FROM polls WHERE id = ? AND status = 'active'", (poll_id,))
        if not rows:
            return False, "Sondage introuvable ou clôturé."
        p = dict(rows[0])
        options = json.loads(p["options_json"])
        if option_idx < 0 or option_idx >= len(options):
            return False, "Option invalide."

        # Retirer un vote précédent
        for opt in options:
            if user_id in opt["votes"]:
                opt["votes"].remove(user_id)

        options[option_idx]["votes"].append(user_id)
        self.db.execute("UPDATE polls SET options_json = ? WHERE id = ?", (json.dumps(options), poll_id))
        return True, f"Votre vote pour **{options[option_idx]['text']}** a été pris en compte !"

    def get_results(self, poll_id: int) -> dict | None:
        rows = self.db.query("SELECT * FROM polls WHERE id = ?", (poll_id,))
        if not rows:
            return None
        p = dict(rows[0])
        p["options"] = json.loads(p["options_json"])
        return p
