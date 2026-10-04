"""Agent autonome de programmation et d'auto-amélioration de NOVA."""

import os
import uuid
from typing import Dict, Any, Tuple
from coding.analyzer import CodeAnalyzer
from coding.validator import CodeValidator
from coding.editor import CodeEditor
from coding.tester import CodeTester
from coding.sandbox import Sandbox
from ai.planner import MissionPlan
from ai.reasoning import ReasoningEngine
from git_agent.manager import GitAgent
from self_improvement.proposals import ImprovementProposal, ProposalRegistry
from self_improvement.history import ImprovementHistory


class CodeAgent:
    """Exécute des missions de code en boucle fermée : Plan -> Sandbox -> Auto-Correct -> Commit."""

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        self.analyzer = CodeAnalyzer(self.root_dir)
        self.validator = CodeValidator()
        self.editor = CodeEditor(self.root_dir, self.validator)
        self.tester = CodeTester(self.root_dir)
        self.reasoning = ReasoningEngine()
        self.git = GitAgent(self.root_dir)
        self.proposals = ProposalRegistry(os.path.join(self.root_dir, "proposals"))
        self.history = ImprovementHistory(os.path.join(self.root_dir, "proposals", "history.json"))

    def create_mission_plan(self, goal: str, target_file: str) -> MissionPlan:
        plan = MissionPlan(str(uuid.uuid4())[:8], goal)
        plan.add_step("OBSERVE", f"Analyser la structure du fichier cible {target_file}", target_file)
        plan.add_step("PLAN", f"Vérifier la validité et la sécurité des modifications", target_file)
        plan.add_step("ACT", f"Appliquer la modification dans le bac à sable (sandbox)", target_file)
        plan.add_step("TEST", f"Exécuter l'ensemble des tests pytest", target_file)
        plan.add_step("EVALUATE", f"Vérifier l'absence de régression", target_file)
        plan.add_step("VERIFY", f"Créer la proposition ou appliquer avec traçabilité", target_file)
        return plan

    def execute_code_improvement(
        self,
        goal: str,
        target_file: str,
        new_content: str,
        auto_commit: bool = False,
    ) -> Dict[str, Any]:
        """Exécute le cycle complet d'auto-amélioration avec validation rigoureuse."""
        plan = self.create_mission_plan(goal, target_file)
        
        # 1. OBSERVE
        step = plan.get_current_step()
        file_analysis = self.analyzer.analyze_file(target_file)
        plan.advance("Analyse effectuée.")

        # 2. PLAN & VALIDATION
        valid, msg = self.validator.validate_change(target_file, new_content)
        if not valid:
            plan.fail_current_step(f"Sécurité: {msg}")
            return {
                "success": False,
                "error": msg,
                "plan": plan.summary(),
            }
        plan.advance("Validation de sécurité validée.")

        # 3 & 4. ACT & TEST DANS SANDBOX
        with Sandbox(self.root_dir) as sandbox:
            sandbox_res = sandbox.test_modification(target_file, new_content)

        test_run = sandbox_res.get("test_results", {})
        if not test_run.get("success", False):
            diagnosis = self.reasoning.analyze_test_failure(
                test_run.get("stdout", ""), test_run.get("stderr", "")
            )
            plan.fail_current_step(f"Tests échoués: {test_run.get('summary')}")
            return {
                "success": False,
                "error": "Les tests ont échoué dans la sandbox.",
                "diagnosis": diagnosis,
                "test_summary": test_run.get("summary"),
                "plan": plan.summary(),
            }
        plan.advance(f"Sandbox OK : {test_run.get('summary')}")
        plan.advance("Aucune régression détectée.")

        # 5. CRÉATION PROPOSITION & APPLICATION CONTRÔLÉE
        proposal_id = f"prop_{plan.mission_id}"
        proposal = ImprovementProposal(
            proposal_id=proposal_id,
            title=goal,
            description=f"Amélioration automatique sur {target_file}",
            target_files=[target_file],
            changes={target_file: new_content},
            status="VALIDATED_IN_SANDBOX",
        )
        self.proposals.save(proposal)

        # Application effective
        write_ok, write_msg = self.editor.write_file(target_file, new_content)
        if not write_ok:
            return {"success": False, "error": write_msg, "plan": plan.summary()}

        proposal.status = "APPLIED"
        self.proposals.save(proposal)

        # Historique
        self.history.record(
            version="v2.0+",
            goal=goal,
            files_modified=[target_file],
            test_summary=test_run.get("summary", ""),
            author="NOVA Code Agent",
        )

        commit_info = None
        if auto_commit:
            branch_name = f"nova/improve-{plan.mission_id}"
            self.git.create_branch(branch_name)
            ok_c, commit_msg = self.git.commit_changes(f"Amélioration : {goal}", [target_file])
            commit_info = {"branch": branch_name, "message": commit_msg}

        plan.advance("Mission accomplie avec succès.")

        return {
            "success": True,
            "proposal_id": proposal_id,
            "target_file": target_file,
            "test_summary": test_run.get("summary"),
            "commit": commit_info,
            "plan": plan.summary(),
        }
