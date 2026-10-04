import pytest
from ai.planner import MissionPlan
from ai.personality import PersonalityEngine
from ai.reasoning import ReasoningEngine

def test_mission_plan_steps():
    plan = MissionPlan("m-101", "Améliorer tournois")
    plan.add_step("OBSERVE", "Lire code")
    plan.add_step("ACT", "Modifier code")
    assert len(plan.steps) == 2
    assert plan.current_index == 0
    assert not plan.is_finished()
    plan.advance("Vu")
    assert plan.current_index == 1
    plan.advance("Fait")
    assert plan.is_finished()

def test_personality_engine_glados_and_apology():
    pe = PersonalityEngine()
    assert pe.is_insult("T'es vraiment nulle Nova")
    assert pe.is_apology("Pardon Nova, je m'excuse")

    g1 = pe.format_glados_response(tier=1)
    assert "ALERTE COMPORTEMENT" in g1
    assert pe.current_mood == "annoyed"

    g2 = pe.format_glados_response(tier=2)
    assert "MODE GLADOS ENGAGÉ" in g2
    assert pe.current_mood == "sarcastic"

    apology_reply = pe.format_apology_response()
    assert "acceptées" in apology_reply or "enregistrées" in apology_reply or "noté" in apology_reply
    assert pe.current_mood == "normal"

def test_reasoning_engine():
    reasoning = ReasoningEngine()
    fake_pytest = "tests/test_demo.py:42: AssertionError\nE   assert 1 == 2"
    diagnosis = reasoning.analyze_test_failure(fake_pytest, "")
    assert diagnosis["error_type"] == "AssertionError"
    assert diagnosis["failed_file"] == "tests/test_demo.py"
    assert diagnosis["failed_line"] == 42
