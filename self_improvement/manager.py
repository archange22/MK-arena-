"""Chef d'orchestre de la boucle d'auto-amélioration contrôlée."""

import os
from typing import Dict, Any, Tuple
from coding.sandbox import Sandbox
from coding.editor import CodeEditor
from self_improvement.proposals import ImprovementProposal, ProposalRegistry
from self_improvement.history import ImprovementHistory
from self_improvement.evaluator import SelfEvaluator
from git_agent.manager import GitAgent


class SelfImprovementManager:
    """Pilote la boucle : Analyse -> Proposition -> Sandbox -> Validation -> Application."""

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        self.registry = ProposalRegistry(os.path.join(self.root_dir, "proposals"))
        self.history = ImprovementHistory(os.path.join(self.root_dir, "proposals", "history.json"))
        self.evaluator = SelfEvaluator(self.root_dir)
        self.editor = CodeEditor(self.root_dir)
        self.git = GitAgent(self.root_dir)

    def create_and_test_proposal(
        self,
        proposal_id: str,
        title: str,
        description: str,
        target_file: str,
        new_content: str,
    ) -> Tuple[bool, ImprovementProposal, Dict[str, Any]]:
        """Valide la proposition dans un bac à sable (sandbox) sans toucher au dépôt principal."""
        proposal = ImprovementProposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            target_files=[target_file],
            changes={target_file: new_content},
            status="PROPOSED",
        )

        with Sandbox(self.root_dir) as sandbox:
            res = sandbox.test_modification(target_file, new_content)

        is_safe = res.get("safe_to_merge", False)
        if not is_safe:
            proposal.status = "REJECTED_TEST_FAILED"
            self.registry.save(proposal)
            return False, proposal, res

        proposal.status = "VALIDATED_IN_SANDBOX"
        self.registry.save(proposal)
        return True, proposal, res

    def apply_proposal(self, proposal_id: str, commit_message: str = None) -> Tuple[bool, str]:
        """Applique définitivement une proposition validée sur le dépôt principal."""
        proposal = self.registry.get(proposal_id)
        if not proposal:
            return False, f"Proposition '{proposal_id}' introuvable."

        if proposal.status not in {"VALIDATED_IN_SANDBOX", "APPROVED"}:
            return False, f"Statut non éligible pour application : {proposal.status}"

        # Écriture des fichiers
        for target, content in proposal.changes.items():
            success, msg = self.editor.write_file(target, content)
            if not success:
                return False, f"Erreur lors de l'application sur '{target}': {msg}"

        # Validation par les tests en local
        eval_res = self.evaluator.evaluate_health()
        if eval_res["status"] != "HEALTHY":
            # Rollback immédiat
            for target in proposal.changes.keys():
                self.editor.rollback(target)
            proposal.status = "ROLLED_BACK"
            self.registry.save(proposal)
            return False, f"Tests échoués après écriture. Rollback automatique exécuté ({eval_res['failed']} échecs)."

        proposal.status = "APPLIED"
        self.registry.save(proposal)

        # Enregistrement dans l'historique
        summary = f"{eval_res['passed']} passed, 0 failed"
        self.history.record(
            version="v2.0+",
            goal=proposal.title,
            files_modified=proposal.target_files,
            test_summary=summary,
        )

        # Git commit si demandé
        if commit_message:
            self.git.commit_changes(commit_message, proposal.target_files)

        return True, f"Proposition '{proposal.title}' appliquée et vérifiée avec succès."
