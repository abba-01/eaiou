"""
Mira — Defender intelligence module.
Loaded into eaiou's module system as the left-side Defender.
Lifecycle: load → read (activates module) → redteam (satisfies RED_TEAM_RAN gate).
"""
from agents.eaiou_client import EaiouClient
from agents.scorch import Scorch
from agents import config


class MiraAgent:
    def __init__(self, client: EaiouClient, scorch: Scorch):
        self.client = client
        self.scorch = scorch
        self.module_id: int | None = None

    def load(self, paper_id: int) -> int:
        """Register Mira as Defender module. Returns module_id."""
        with self.scorch.step("mira_load"):
            result = self.client.add_module(
                paper_id=paper_id,
                role="defender",
                display_label="Mira",
                model_id=config.MODEL_MIRA,
            )
            self.module_id = result["module_id"]
            self.scorch.info(f"Mira registered: module_id={self.module_id}", step="mira_load")
            return self.module_id

    def read(self, paper_id: int) -> dict:
        """
        Mira reads the document.
        Changes module status from not_loaded → active.
        MUST happen before redteam (server enforces status check).
        """
        with self.scorch.step("mira_read"):
            result = self.client.module_read(paper_id, self.module_id)
            self.scorch.info("Mira read complete — module now active", step="mira_read")
            return result

    def redteam(self, paper_id: int, focus: str = "") -> dict:
        """
        Mira red-teams the document.
        Writes event_type='red_team' to #__eaiou_module_events → satisfies RED_TEAM_RAN gate.
        """
        with self.scorch.step("mira_redteam"):
            result = self.client.module_redteam(paper_id, self.module_id, focus=focus)
            self.scorch.info("Mira red-team done — RED_TEAM_RAN gate satisfied", step="mira_redteam")
            return result
