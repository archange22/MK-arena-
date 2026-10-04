"""Task Planner: generates sequence of subtasks from user goal"""
from agent.task import Task

class AgentPlanner:
    @staticmethod
    def plan_mission(goal: str, creator_id: int = 0) -> Task:
        task = Task(goal, creator_id)
        task.add_step(f"Observation et analyse du besoin : {goal}")
        task.add_step("Recherche des fichiers et du contexte")
        task.add_step("Génération et application des modifications")
        task.add_step("Exécution de la suite de tests en sandbox")
        task.add_step("Revue de code de sécurité et d'optimisation")
        task.add_step("Commit et enregistrement de la proposition")
        return task
