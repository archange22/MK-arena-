import pytest
from ai.code_agent import CodeAgent

def test_code_agent_security_blocks_protected_file():
    agent = CodeAgent('/tmp/MK-arena-')
    res = agent.execute_code_improvement(
        "Hacker permissions",
        "security/permissions.py",
        "def bypass():\n    return True\n"
    )
    assert res["success"] is False
    assert "protégé" in res["error"]

def test_code_agent_security_blocks_dangerous_code():
    agent = CodeAgent('/tmp/MK-arena-')
    res = agent.execute_code_improvement(
        "Code malveillant",
        "features/dummy.py",
        "import os\nos.system('rm -rf /')\n"
    )
    assert res["success"] is False
    assert "motifs dangereux" in res["error"]
