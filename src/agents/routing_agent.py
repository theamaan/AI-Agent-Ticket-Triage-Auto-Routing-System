"""
Routing Agent — maps category → team + individual assignee.
Primary: Excel routing_config.xlsx lookup.
Secondary: Ollama refines individual when multiple assignees available.
"""
from __future__ import annotations

import logging
import random
from pathlib import Path
from typing import Optional

import pandas as pd

from src.agents.base_agent import OllamaAgent
from src.config.settings import settings

logger = logging.getLogger(__name__)

# Category → team mapping (must stay in sync with classifier categories)
CATEGORY_TO_TEAM: dict[str, str] = {
    # Testing Team
    "Test case failure": "Testing Team",
    "Regression test blocked": "Testing Team",
    "UAT environment issue": "Testing Team",
    "Automation script error": "Testing Team",
    "Test data missing": "Testing Team",
    "QA sign-off pending": "Testing Team",
    "Performance test failure": "Testing Team",
    # EDI Team
    "EDI transaction error": "EDI Team",
    "835 file not received": "EDI Team",
    "837 claim rejection": "EDI Team",
    "EDI partner connectivity": "EDI Team",
    "HIPAA validation failure": "EDI Team",
    "EDI mapping issue": "EDI Team",
    "Acknowledgement not received": "EDI Team",
    "Trading partner setup": "EDI Team",
    # BizTalk Team
    "BizTalk orchestration failure": "BizTalk Team",
    "Message routing error": "BizTalk Team",
    "BizTalk pipeline exception": "BizTalk Team",
    "Suspended message in BizTalk": "BizTalk Team",
    "BizTalk adapter configuration": "BizTalk Team",
    "Schema validation error": "BizTalk Team",
    "BizTalk host instance down": "BizTalk Team",
    "Tracking database issue": "BizTalk Team",
    # Database Team
    "Database connection timeout": "Database Team",
    "Slow query performance": "Database Team",
    "Deadlock detected": "Database Team",
    "Backup job failure": "Database Team",
    "Data integrity issue": "Database Team",
    "Stored procedure error": "Database Team",
    "Database migration failure": "Database Team",
    "Disk space alert on DB server": "Database Team",
    "Index rebuild needed": "Database Team",
    "Replication lag": "Database Team",
    # Network
    "VPN connectivity issue": "Network Team",
    "Network latency spike": "Network Team",
    "Firewall rule blocking traffic": "Network Team",
    "DNS resolution failure": "Network Team",
    "Load balancer misconfiguration": "Network Team",
    # Access
    "User account locked": "Access Team",
    "Password reset request": "Access Team",
    "Permission denied on folder": "Access Team",
    "MFA not working": "Access Team",
    "New user onboarding access": "Access Team",
    # Security
    "Suspicious login attempt": "Security Team",
    "Malware detected on endpoint": "Security Team",
    "Phishing email reported": "Security Team",
    "Security patch deployment": "Security Team",
    "Compliance audit finding": "Security Team",
}


class RoutingAgent(OllamaAgent):

    def __init__(self) -> None:
        super().__init__()
        self._routing_df: Optional[pd.DataFrame] = None
        self._leads_df: Optional[pd.DataFrame] = None

    def _load_routing_config(self) -> None:
        path = Path(settings.routing_config_path)
        if not path.exists():
            logger.warning("routing_config.xlsx not found at %s. Routing will use defaults.", path)
            return
        try:
            self._routing_df = pd.read_excel(path, sheet_name="Routing", engine="openpyxl")
            self._leads_df = pd.read_excel(path, sheet_name="TeamLeads", engine="openpyxl")
        except Exception as exc:
            logger.error("Failed to load routing config: %s", exc)

    def _get_team_members(self, team: str) -> list[dict]:
        if self._routing_df is None:
            self._load_routing_config()
        if self._routing_df is None:
            return []
        rows = self._routing_df[self._routing_df["Team"] == team]
        return rows.to_dict("records")

    def _get_team_lead_email(self, team: str) -> str:
        if self._leads_df is None:
            self._load_routing_config()
        if self._leads_df is None:
            return ""
        rows = self._leads_df[self._leads_df["Team"] == team]
        if rows.empty:
            return ""
        return str(rows.iloc[0].get("Lead_Email", ""))

    async def route(self, category: str, priority: str, summary: str) -> dict:
        """
        Returns:
            {
                "team": str,
                "assignee": str,
                "assignee_email": str,
                "team_lead_email": str,
            }
        """
        team = CATEGORY_TO_TEAM.get(category, "Testing Team")
        members = self._get_team_members(team)

        if not members:
            # Fallback defaults if routing config not loaded
            return {
                "team": team,
                "assignee": "Team Lead",
                "assignee_email": "",
                "team_lead_email": "",
            }

        # For P1/P2 — always assign to team lead (first member)
        if priority in ("P1", "P2"):
            lead = members[0]
            return {
                "team": team,
                "assignee": lead["Assignee"],
                "assignee_email": lead["Email"],
                "team_lead_email": self._get_team_lead_email(team),
            }

        # For P3/P4 — ask LLM to pick best assignee based on context
        if len(members) == 1:
            chosen = members[0]
        else:
            chosen = await self._llm_pick_assignee(summary, members) or random.choice(members)

        return {
            "team": team,
            "assignee": chosen["Assignee"],
            "assignee_email": chosen.get("Email", ""),
            "team_lead_email": self._get_team_lead_email(team),
        }

    async def _llm_pick_assignee(self, summary: str, members: list[dict]) -> Optional[dict]:
        members_str = "\n".join(
            f"  - {m['Assignee']} ({m.get('Role', 'N/A')})" for m in members
        )
        prompt = (
            f"Choose the most appropriate assignee for this IT ticket.\n\n"
            f"Ticket Summary: {summary}\n\n"
            f"Available assignees:\n{members_str}\n\n"
            f"Return JSON with key: assignee (exact name from list)."
            f"{self._build_json_instruction()}"
        )
        raw = await self._call_ollama(prompt)
        result = self._parse_json_response(raw, {})
        chosen_name = result.get("assignee", "")
        for m in members:
            if m["Assignee"] == chosen_name:
                return m
        return None
