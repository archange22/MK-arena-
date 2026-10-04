"""Planificateur multi-étapes pour les missions autonomes de NOVA."""

import time
from typing import List, Dict, Any, Optional


class PlanStep:
    """Représente une étape unitaire d'un plan."""

    def __init__(self, step_id: int, action: str, description: str, target: str = ""):
        self.step_id = step_id
        self.action = action  # OBSERVE, PLAN, ACT, TEST, CORRECT, VERIFY, DONE
        self.description = description
        self.target = target
        self.status = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED, FAILED
        self.result: Optional[str] = None
        self.retries = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "action": self.action,
            "description": self.description,
            "target": self.target,
            "status": self.status,
            "result": self.result,
            "retries": self.retries,
        }


class MissionPlan:
    """Gère l'ordonnancement, la progression et la reprise après interruption."""

    def __init__(self, mission_id: str, goal: str):
        self.mission_id = mission_id
        self.goal = goal
        self.steps: List[PlanStep] = []
        self.current_index = 0
        self.created_at = time.strftime("%Y-%m-%d %H:%M:%S")

    def add_step(self, action: str, description: str, target: str = "") -> PlanStep:
        step = PlanStep(len(self.steps) + 1, action, description, target)
        self.steps.append(step)
        return step

    def get_current_step(self) -> Optional[PlanStep]:
        if 0 <= self.current_index < len(self.steps):
            return self.steps[self.current_index]
        return None

    def advance(self, result: str = "OK"):
        step = self.get_current_step()
        if step:
            step.status = "COMPLETED"
            step.result = result
            self.current_index += 1

    def fail_current_step(self, error: str):
        step = self.get_current_step()
        if step:
            step.status = "FAILED"
            step.result = error
            step.retries += 1

    def is_finished(self) -> bool:
        return self.current_index >= len(self.steps)

    def summary(self) -> str:
        lines = [f"Plan pour la mission '{self.goal}' ({len(self.steps)} étapes) :"]
        for s in self.steps:
            icon = "✅" if s.status == "COMPLETED" else ("🔄" if s.status == "IN_PROGRESS" else ("❌" if s.status == "FAILED" else "⏳"))
            lines.append(f"{icon} Étape {s.step_id} [{s.action}]: {s.description}")
        return "\n".join(lines)
