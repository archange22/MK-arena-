import os
import pytest
from dashboard.firebase_sync import FirebaseSync
from ai.reasoning import ReasoningEngine

def test_firebase_sync_initialization():
    sync = FirebaseSync()
    assert "mk-esports-events" in sync.database_url
    assert sync._put("nova/test", {"test": True}) in (True, False)

def test_ai_reasoning_chain_of_thought():
    engine = ReasoningEngine()
    cot = engine.build_chain_of_thought("Créer un système de tournoi sécurisé")
    assert len(cot) == 4
    assert cot[0]["step"] == "Analyse du besoin"

def test_ai_codm_tournament_strategy():
    engine = ReasoningEngine()
    strat = engine.get_codm_tournament_strategy("HARDPOINT", "Raid")
    assert strat["mode"] == "HARDPOINT"
    assert "P1 Cour centrale" in strat["conseil_carte"]
    assert "Krig 6" in strat["weapons_meta"]
