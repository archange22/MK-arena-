"""Comprehensive unit tests for NOVA v2.1 -> v5.0 modular architecture"""
import pytest
from core.nova import NovaCore
from core.lifecycle import LifecycleManager
from core.config import NovaConfig
from ai.local_engine import LocalAIEngine
from ai.structured_output import StructuredOutputParser
from memory.semantic import SemanticSearch
from memory.user_memory import UserMemory
from memory.server_memory import ServerMemory
from memory.forgetting import ForgettingEngine
from personality.mood import MoodManager, MoodState
from personality.behavior import BehaviorStylizer
from personality.insults import InsultDetector
from tools.manager import ToolManager
from coding.patcher import CodePatcher
from coding.reviewer import CodeReviewer
from agent.task import Task
from agent.planner import AgentPlanner
from agent.supervisor import TaskSupervisor
from agent.executor import TaskExecutor
from self_improvement.experiments import ExperimentRunner
from git_manager.repository import GitRepository
from security.secrets import SecretScanner
from dashboard.api.routes import DashboardAPI

def test_core_and_lifecycle():
    core = NovaCore()
    status = core.status()
    assert status["version"] == "5.0.0-alpha"
    assert status["health"]["status"] == "READY"
    assert "Message received" in core.process_message(1, 1, "Salut")

def test_ai_local_and_structured():
    engine = LocalAIEngine(model_name="test-model")
    res = StructuredOutputParser.parse_json('{"goal": "test", "val": 42}')
    assert res == {"goal": "test", "val": 42}
    assert StructuredOutputParser.enforce_schema(res, ["goal", "val"]) is True
    assert StructuredOutputParser.enforce_schema(res, ["nonexistent"]) is False

def test_memory_systems():
    docs = [
        {"id": 1, "content": "Tournoi MK SQUID GAME le 16 octobre"},
        {"id": 2, "content": "Règles de modération anti-raid"},
        {"id": 3, "content": "Astuces Call of Duty Mobile Hardpoint"}
    ]
    ranked = SemanticSearch.rank("squid game tournoi", docs, key="content")
    assert len(ranked) > 0
    assert ranked[0][1]["id"] == 1

    forgetting = ForgettingEngine(default_ttl=100)
    assert forgetting.is_expired(0, importance=1.0) is True

def test_personality_and_insults():
    mood_mgr = MoodManager()
    assert mood_mgr.get_mood() == MoodState.NORMAL
    mood_mgr.set_mood(MoodState.SARCASTIC)
    assert mood_mgr.get_mood() == MoodState.SARCASTIC

    styled = BehaviorStylizer.apply_style("Je refuse.", MoodState.COLD)
    assert "Mode Glacial" in styled

    assert InsultDetector.is_insult("ferme ta gueule") is True
    assert InsultDetector.is_apology("Pardon Nova je m'excuse") is True
    assert InsultDetector.is_insult("Le Hardpoint est difficile") is False

def test_tools_system():
    mgr = ToolManager()
    mgr.register_tool("add", lambda a, b: a + b, {"type": "math"}, permission_level="admin")
    result = mgr.execute("add", {"a": 10, "b": 32})
    assert result == 42
    assert len(mgr.execution_log) == 1

def test_coding_patcher_and_reviewer():
    orig = "def hello():\n    return 1\n"
    mod = "def hello():\n    return 2\n"
    diff = CodePatcher.create_diff(orig, mod)
    assert "-    return 1" in diff
    assert "+    return 2" in diff

    patched = CodePatcher.apply_patch(orig, "return 1", "return 42")
    assert "return 42" in patched

    rev_clean = CodeReviewer.review_code("def add(a, b): return a + b")
    assert rev_clean["valid"] is True

    rev_risky = CodeReviewer.review_code("import pickle\neval('1+1')")
    assert rev_risky["valid"] is False
    assert len(rev_risky["issues"]) >= 2

def test_agent_task_and_executor():
    task = AgentPlanner.plan_mission("Ajouter un module de log", creator_id=123)
    assert len(task.steps) == 6
    assert task.status.value == "PENDING"

    executor = TaskExecutor()
    executed_task = executor.execute_task(task)
    assert executed_task.status.value == "COMPLETED"
    assert all(s.status.value == "COMPLETED" for s in executed_task.steps)

    risky_task = Task("rm -rf all database", creator_id=999)
    assert TaskSupervisor.requires_approval(risky_task) is True

def test_security_secrets():
    leak_text = "Voici mon token secret: ghp_123456789012345678901234567890123456"
    assert SecretScanner.contains_secret(leak_text) is True
    sanitized = SecretScanner.sanitize(leak_text)
    assert "[REDACTED SECRET]" in sanitized

def test_dashboard_api():
    api = DashboardAPI()
    st = api.get_status()
    assert st["status"] == "ONLINE"
    assert st["version"] == "5.0.0-alpha"
    metrics = api.get_metrics()
    assert metrics["test_success_rate"] == 100.0
    tasks = api.get_tasks()
    assert len(tasks) >= 2
