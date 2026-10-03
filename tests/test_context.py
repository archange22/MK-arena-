from ai.engine import NovaEngine


class DummyContext:
    def latest_tournament_hint(self, user_id):
        return "MK SQUID GAME"


class DummyKnowledge:
    def search_tournaments(self, query, guild_id):
        return [{
            "id": 1,
            "name": "MK SQUID GAME",
            "prizepool": "250 €",
            "teams": "16",
            "format": "BO3",
            "rules": "Règles de base du tournoi",
            "status": "En cours"
        }]

    def get_tournament_details(self, tournament_id):
        return {
            "id": 1,
            "name": "MK SQUID GAME",
            "prizepool": "250 €",
            "teams": "16",
            "format": "BO3",
            "rules": "Règles de base du tournoi",
            "status": "En cours"
        }


def test_context_hint_used_for_tournament_answers():
    engine = NovaEngine(DummyKnowledge(), DummyContext())
    answer = engine.respond(1, 1, "nova et le prizepool ?", reference_context="MK SQUID GAME")
    assert "250" in answer
