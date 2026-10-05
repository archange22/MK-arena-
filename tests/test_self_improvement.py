import os
import pytest
from self_improvement.evaluator import SelfEvaluator
from self_improvement.proposals import ImprovementProposal, ProposalRegistry
from coding.tester import CodeTester

def test_evaluator_health():
    tester = CodeTester(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    res = tester.run_tests('tests/test_context.py', timeout=20)
    assert res["success"] is True
    assert res["passed"] == 3

def test_proposals_registry():
    reg = ProposalRegistry(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'proposals')))
    prop = ImprovementProposal("prop_001", "Optimisation", "Test", ["ai/engine.py"], {"ai/engine.py": ""})
    reg.save(prop)
    loaded = reg.get("prop_001")
    assert loaded is not None
    assert loaded.title == "Optimisation"
