import json

class DraftSystem:
    def __init__(self, db):
        self.db = db

    def create_draft(self, guild_id: int, captain1_id: int, captain2_id: int, bo_type: str = "BO3") -> int:
        cur = self.db.execute(
            """INSERT INTO competitive_drafts (guild_id, captain1_id, captain2_id, bo_type, state, pool_json, team1_json, team2_json, bans_json)
               VALUES (?, ?, ?, ?, 'recruiting', '[]', '[]', '[]', '[]')""",
            (guild_id, captain1_id, captain2_id, bo_type)
        )
        return cur

    def get_draft(self, draft_id: int) -> dict | None:
        rows = self.db.query("SELECT * FROM competitive_drafts WHERE id = ?", (draft_id,))
        if not rows:
            return None
        d = dict(rows[0])
        d["pool"] = json.loads(d["pool_json"] or "[]")
        d["team1"] = json.loads(d["team1_json"] or "[]")
        d["team2"] = json.loads(d["team2_json"] or "[]")
        d["bans"] = json.loads(d["bans_json"] or "[]")
        return d

    def join_pool(self, draft_id: int, user_id: int) -> tuple[bool, str]:
        draft = self.get_draft(draft_id)
        if not draft:
            return False, "Draft introuvable."
        if draft["state"] != "recruiting":
            return False, "Le draft n'accepte plus d'inscriptions."
        pool = draft["pool"]
        if user_id in pool or user_id == draft["captain1_id"] or user_id == draft["captain2_id"]:
            return False, "Vous participez déjà à ce draft."
        pool.append(user_id)
        self.db.execute("UPDATE competitive_drafts SET pool_json = ? WHERE id = ?", (json.dumps(pool), draft_id))
        return True, f"Inscription validée ! Total joueurs en pool : {len(pool)}."

    def start_picking(self, draft_id: int) -> tuple[bool, str]:
        draft = self.get_draft(draft_id)
        if not draft:
            return False, "Draft introuvable."
        if len(draft["pool"]) < 2:
            return False, "Il faut au moins 2 joueurs dans la pool pour lancer la sélection."
        self.db.execute("UPDATE competitive_drafts SET state = 'picking' WHERE id = ?", (draft_id,))
        return True, f"Phase de sélection lancée ! Capitaine 1 (<@{draft['captain1_id']}>), choisissez votre premier joueur."

    def pick_player(self, draft_id: int, captain_id: int, picked_user_id: int) -> tuple[bool, str]:
        draft = self.get_draft(draft_id)
        if not draft or draft["state"] != "picking":
            return False, "Phase de sélection inactive."
        
        is_cap1 = captain_id == draft["captain1_id"]
        is_cap2 = captain_id == draft["captain2_id"]
        if not (is_cap1 or is_cap2):
            return False, "Seuls les capitaines peuvent choisir des joueurs."

        pool = draft["pool"]
        if picked_user_id not in pool:
            return False, "Ce joueur n'est pas ou plus disponible dans la pool."

        pool.remove(picked_user_id)
        team1 = draft["team1"]
        team2 = draft["team2"]

        if is_cap1:
            team1.append(picked_user_id)
            target_team = "Équipe 1"
        else:
            team2.append(picked_user_id)
            target_team = "Équipe 2"

        new_state = "picking" if pool else "banning"
        self.db.execute(
            "UPDATE competitive_drafts SET pool_json = ?, team1_json = ?, team2_json = ?, state = ? WHERE id = ?",
            (json.dumps(pool), json.dumps(team1), json.dumps(team2), new_state, draft_id)
        )
        next_hint = "Toutes les équipes sont complètes ! Passage aux bans de maps/armes." if new_state == "banning" else f"Joueurs restants : {len(pool)}."
        return True, f"<@{picked_user_id}> rejoint {target_team}. {next_hint}"

    def ban_element(self, draft_id: int, captain_id: int, element_name: str) -> tuple[bool, str]:
        draft = self.get_draft(draft_id)
        if not draft:
            return False, "Draft introuvable."
        if draft["state"] != "banning":
            return False, "Le draft n'est pas en phase de ban."
        if captain_id not in (draft["captain1_id"], draft["captain2_id"]):
            return False, "Seuls les capitaines peuvent bannir des maps ou armes."

        bans = draft["bans"]
        bans.append({"banned_by": captain_id, "element": element_name})
        self.db.execute("UPDATE competitive_drafts SET bans_json = ? WHERE id = ?", (json.dumps(bans), draft_id))
        return True, f"🚫 **{element_name}** a été banni pour ce match !"

    def end_draft(self, draft_id: int) -> bool:
        self.db.execute("UPDATE competitive_drafts SET state = 'completed' WHERE id = ?", (draft_id,))
        return True
