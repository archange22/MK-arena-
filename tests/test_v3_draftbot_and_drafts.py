import pytest
from memory.database import Database
from systems.economy import EconomySystem
from systems.drafts import DraftSystem
from systems.giveaways import GiveawaySystem
from systems.polls import PollSystem
from systems.suggestions import SuggestionSystem

@pytest.fixture
def db():
    database = Database(":memory:")
    database.initialize()
    return database

def test_economy_system(db):
    eco = EconomySystem(db)
    acc = eco.get_account(100, 1)
    assert acc["wallet"] == 100

    # Daily
    ok, msg, earned = eco.claim_daily(100, 1)
    assert ok is True
    assert earned == 250
    # Duplicate daily blocked
    ok2, msg2, _ = eco.claim_daily(100, 1)
    assert ok2 is False

    # Work
    ok_work, _, work_earned = eco.work(100, 1)
    assert ok_work is True
    assert work_earned > 0

    # Transfer
    eco.get_account(100, 2)
    ok_t, msg_t = eco.transfer(100, 1, 2, 50)
    assert ok_t is True
    assert eco.get_account(100, 2)["wallet"] == 150

    # Leaderboard
    lb = eco.get_leaderboard(100)
    assert len(lb) == 2

def test_draft_system(db):
    ds = DraftSystem(db)
    draft_id = ds.create_draft(guild_id=100, captain1_id=10, captain2_id=20, bo_type="BO3")
    assert draft_id > 0

    # Join pool
    ok, msg = ds.join_pool(draft_id, user_id=30)
    assert ok is True
    ds.join_pool(draft_id, user_id=40)

    # Start picking
    ok, msg = ds.start_picking(draft_id)
    assert ok is True

    # Captain 1 picks player 30
    ok, msg = ds.pick_player(draft_id, captain_id=10, picked_user_id=30)
    assert ok is True
    d = ds.get_draft(draft_id)
    assert 30 in d["team1"]

    # Captain 2 picks player 40
    ok, msg = ds.pick_player(draft_id, captain_id=20, picked_user_id=40)
    assert ok is True
    d = ds.get_draft(draft_id)
    assert 40 in d["team2"]
    assert d["state"] == "banning"

    # Ban map / weapon
    ok, msg = ds.ban_element(draft_id, captain_id=10, element_name="Firing Range")
    assert ok is True
    d = ds.get_draft(draft_id)
    assert any(b["element"] == "Firing Range" for b in d["bans"])

def test_giveaway_and_polls(db):
    gw = GiveawaySystem(db)
    gid = gw.start_giveaway(100, 555, prize="Pass de Combat CODM", winners=1, duration_sec=3600)
    assert gid > 0

    ok, msg = gw.enter_giveaway(gid, user_id=1)
    assert ok is True
    ok, winners, prize = gw.draw_winners(gid)
    assert ok is True
    assert winners == [1]

    # Polls
    ps = PollSystem(db)
    pid = ps.create_poll(100, "Meilleure arme SMG ?", ["CBR4", "Fennec", "Switchblade"])
    assert pid > 0

    ok, msg = ps.vote(pid, user_id=1, option_idx=0)
    assert ok is True
    res = ps.get_results(pid)
    assert len(res["options"][0]["votes"]) == 1

def test_suggestions_system(db):
    sug = SuggestionSystem(db)
    sid = sug.add_suggestion(100, 1, "Ajouter un mode 1v1 Sniper")
    assert sid > 0
    ok, up, down = sug.vote_suggestion(sid, user_id=2, up=True)
    assert ok is True
    assert up == 1
