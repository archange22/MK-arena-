"""Gestionnaire des propositions d'auto-amélioration."""

import os
import json
import time
from typing import List, Dict, Any, Optional


class ImprovementProposal:
    """Modèle d'une proposition d'amélioration autonome."""

    def __init__(
        self,
        proposal_id: str,
        title: str,
        description: str,
        target_files: List[str],
        changes: Dict[str, str],
        status: str = "PROPOSED",
    ):
        self.id = proposal_id
        self.title = title
        self.description = description
        self.target_files = target_files
        self.changes = changes
        self.status = status
        self.created_at = time.strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "target_files": self.target_files,
            "changes": self.changes,
            "status": self.status,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImprovementProposal":
        p = cls(
            proposal_id=data["id"],
            title=data["title"],
            description=data["description"],
            target_files=data["target_files"],
            changes=data["changes"],
            status=data.get("status", "PROPOSED"),
        )
        p.created_at = data.get("created_at", "")
        return p


class ProposalRegistry:
    """Stocke et historise les propositions sous proposals/."""

    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def save(self, proposal: ImprovementProposal) -> str:
        file_path = os.path.join(self.storage_dir, f"{proposal.id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(proposal.to_dict(), f, indent=2, ensure_ascii=False)
        return file_path

    def get(self, proposal_id: str) -> Optional[ImprovementProposal]:
        file_path = os.path.join(self.storage_dir, f"{proposal_id}.json")
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ImprovementProposal.from_dict(data)

    def list_all(self) -> List[ImprovementProposal]:
        proposals = []
        for f in os.listdir(self.storage_dir):
            if f.endswith(".json"):
                p = self.get(f.removesuffix(".json"))
                if p:
                    proposals.append(p)
        return sorted(proposals, key=lambda x: x.created_at, reverse=True)
