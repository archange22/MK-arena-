"""Task supervisor: enforces safety, human gates and resource budgets"""
from agent.state import TaskState
from agent.task import Task

class TaskSupervisor:
    RISKY_KEYWORDS = ["rm", "delete", "drop", "destroy", "push --force", "rebase"]

    @classmethod
    def requires_approval(cls, task: Task) -> bool:
        goal_low = task.goal.lower()
        return any(k in goal_low for k in cls.RISKY_KEYWORDS)

    @classmethod
    def check_task(cls, task: Task) -> bool:
        if cls.requires_approval(task) and task.status != TaskState.COMPLETED:
            task.status = TaskState.AWAITING_APPROVAL
            return False
        return True
