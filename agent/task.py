"""Task and step models"""
import uuid
import time
from typing import List, Dict, Any, Optional
from agent.state import TaskState

class TaskStep:
    def __init__(self, step_id: int, description: str, tool_name: Optional[str] = None, tool_args: Optional[dict] = None):
        self.step_id = step_id
        self.description = description
        self.tool_name = tool_name
        self.tool_args = tool_args or {}
        self.status = TaskState.PENDING
        self.result = None
        self.error = None

class Task:
    def __init__(self, goal: str, creator_id: int = 0):
        self.task_id = str(uuid.uuid4())[:8]
        self.goal = goal
        self.creator_id = creator_id
        self.created_at = time.time()
        self.status = TaskState.PENDING
        self.steps: List[TaskStep] = []
        self.current_step_index = 0
        self.result = None

    def add_step(self, description: str, tool_name: Optional[str] = None, tool_args: Optional[dict] = None) -> TaskStep:
        step = TaskStep(len(self.steps) + 1, description, tool_name, tool_args)
        self.steps.append(step)
        return step

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "status": self.status.value,
            "created_at": self.created_at,
            "steps": [
                {"id": s.step_id, "desc": s.description, "status": s.status.value, "result": s.result}
                for s in self.steps
            ]
        }
