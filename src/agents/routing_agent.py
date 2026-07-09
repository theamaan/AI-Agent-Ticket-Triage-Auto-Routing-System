"""
Routing Agent — two-stage routing:

  Stage 1 — Team:
    Look up the AI-classified category in TEAM_CATEGORIES to determine
    which of the 7 teams owns the ticket.  Default → Testing Team.

  Stage 2 — Member (EDI Team only):
    When the ticket belongs to EDI Team, search the ticket summary text
    for keywords defined in data/edi_routing.json and assign the matching
    member.  For all other teams no individual member is assigned.

To add/change EDI member keywords edit data/edi_routing.json only.
To add/change team categories edit TEAM_CATEGORIES below only.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from src.agents.base_agent import OllamaAgent

logger = logging.getLogger(__name__)

# ── Team → category mapping ───────────────────────────────────────────────────
# Each list entry is a category string the classifier may return.
# For EDI Team the list also contains the raw member keywords from
# edi_routing.json so that keyword-labelled tickets are captured here too.
TEAM_CATEGORIES: dict[str, list[str]] = {
    "Testing Team": [
        "Test case failure",
        "Regression test blocked",
        "UAT environment issue",
        "Automation script error",
        "Test data missing",
        "QA sign-off pending",
        "Performance test failure",
    ],
    "EDI Team": [
        # Standard EDI classifier categories
        "EDI transaction error",
        "835 file not received",
        "837 claim rejection",
        "EDI partner connectivity",
        "HIPAA validation failure",
        "EDI mapping issue",
        "Acknowledgement not received",
        "Trading partner setup",
        # Member keywords from edi_routing.json (Ulavapati Haritha)
        "mmw", "ssis", "ssrs",
        # Member keywords (Gopichand Karumuri)
        "27x", "servicebus", "dotnet upgrade",
        # Member keywords (Sindhura Bayapureddy)
        "eutf", "pex", "834", "835", "tumbleweed",
        # Member keywords (Nawin Udhayakumar)
        "biztalk", "dsvalid", "dsinvalid",
        # Member keywords (Arunkumar Kumarasamy)
        "meg", "tidal",
        # Member keywords (Ganti Sri Harshini)
        "mcg", "ecrtp", "crtp",
        # Member keywords (Pretheeba Udayakumar)
        "captiva", "ack service",
        # Member keywords (Saivardhan Manikonda)
        "initial 999", "837",
        # Member keywords (Sankalp Maheshwari)
        "final 999", "277ca", "x12data",
    ],
    "BizTalk Team": [
        "BizTalk orchestration failure",
        "Message routing error",
        "BizTalk pipeline exception",
        "Suspended message in BizTalk",
        "BizTalk adapter configuration",
        "Schema validation error",
        "BizTalk host instance down",
        "Tracking database issue",
    ],
    "Database Team": [
        "Database connection timeout",
        "Slow query performance",
        "Deadlock detected",
        "Backup job failure",
        "Data integrity issue",
        "Stored procedure error",
        "Database migration failure",
        "Disk space alert on DB server",
        "Index rebuild needed",
        "Replication lag",
    ],
    "Network Team": [
        "VPN connectivity issue",
        "Network latency spike",
        "Firewall rule blocking traffic",
        "DNS resolution failure",
        "Load balancer misconfiguration",
    ],
    "Access Team": [
        "User account locked",
        "Password reset request",
        "Permission denied on folder",
        "MFA not working",
        "New user onboarding access",
    ],
    "Security Team": [
        "Suspicious login attempt",
        "Malware detected on endpoint",
        "Phishing email reported",
        "Security patch deployment",
        "Compliance audit finding",
    ],
}

# Reverse lookup: category (lowercased) → team — built once at import time
_CATEGORY_TO_TEAM: dict[str, str] = {
    cat.lower(): team
    for team, cats in TEAM_CATEGORIES.items()
    for cat in cats
}

# ── EDI member config ─────────────────────────────────────────────────────────
_CONFIG_PATH = Path(__file__).resolve().parents[2] / "data" / "edi_routing.json"
_edi_config: Optional[dict] = None


def _load_edi_config() -> dict:
    global _edi_config
    if _edi_config is not None:
        return _edi_config
    if not _CONFIG_PATH.exists():
        logger.warning("edi_routing.json not found at %s — EDI members will be Unassigned.", _CONFIG_PATH)
        _edi_config = {"team_lead_email": "", "members": []}
        return _edi_config
    try:
        with _CONFIG_PATH.open(encoding="utf-8") as fh:
            _edi_config = json.load(fh)
        logger.info("Loaded EDI routing config: %d members", len(_edi_config.get("members", [])))
    except Exception as exc:
        logger.error("Failed to load edi_routing.json: %s", exc)
        _edi_config = {"team_lead_email": "", "members": []}
    return _edi_config


def _match_edi_member(summary: str) -> tuple[str, str]:
    """Return (member_name, member_email) for the first keyword match, or ('Unassigned', '')."""
    config = _load_edi_config()
    text = summary.lower()
    for member in config.get("members", []):
        for keyword in member.get("keywords", []):
            if keyword.lower() in text:
                return member["name"], member.get("email", "")
    return "Unassigned", ""


# ── Agent class ───────────────────────────────────────────────────────────────

class RoutingAgent(OllamaAgent):

    async def route(self, category: str, priority: str, summary: str) -> dict:
        """
        Stage 1: resolve team from category via TEAM_CATEGORIES.
        Stage 2: if EDI Team, resolve individual member from edi_routing.json keywords.

        Returns:
            {
                "team": str,
                "assignee": str,          # member name (EDI) or "" (other teams)
                "assignee_email": str,
                "team_lead_email": str,
            }
        """
        team = _CATEGORY_TO_TEAM.get(category.lower(), "Testing Team")
        config = _load_edi_config()
        team_lead_email = config.get("team_lead_email", "")

        if team == "EDI Team":
            assignee, assignee_email = _match_edi_member(summary)
        else:
            assignee, assignee_email = "", ""

        return {
            "team": team,
            "assignee": assignee,
            "assignee_email": assignee_email,
            "team_lead_email": team_lead_email,
        }
