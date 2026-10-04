"""Task Executor: runs planned steps and coordinates tools"""
from agent.task import Task
from agent.state import TaskState
from agent.supervisor import TaskSupervisor

class TaskExecutor:
    def __init__(self, tool_manager=None):
        self.tool_manager = tool_manager

    def execute_task(self, task: Task) -> Task:
        if not TaskSupervisor.check_task(task):
            return task

        task.status = TaskState.RUNNING
        for step in task.steps:
            step.status = TaskState.RUNNING
            try:
                if step.tool_name and self.tool_manager:
                    res = self.tool_manager.execute(step.tool_name, step.tool_args)
                    step.result = res
                else:
                    step.result = f"Étape complétée avec succès : {step.description}"
                step.status = TaskState.COMPLETED
            except Exception as e:
                step.status = TaskState.FAILED
                step.error = str(e)
                task.status = TaskState.FAILED
                return task

        task.status = TaskState.COMPLETED
        return task
