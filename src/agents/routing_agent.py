"""
Routing Agent — maps ticket text → EDI Team member via keyword matching.

Assignment configuration is loaded from data/edi_routing.json.
To change member assignments or add/remove keywords, edit that file only —
no code changes are required.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from src.agents.base_agent import OllamaAgent

logger = logging.getLogger(__name__)

# Config path is resolved relative to this file's location (src/agents/ → project root)
_CONFIG_PATH = Path(__file__).resolve().parents[2] / "data" / "edi_routing.json"

# Module-level cache — loaded once on first call, shared across all instances
_edi_config: Optional[dict] = None


def _load_edi_config() -> dict:
    global _edi_config
    if _edi_config is not None:
        return _edi_config
    if not _CONFIG_PATH.exists():
        logger.warning(
            "edi_routing.json not found at %s — all tickets will be Unassigned.", _CONFIG_PATH
        )
        _edi_config = {"team": "EDI Team", "team_lead_email": "", "members": []}
        return _edi_config
    try:
        with _CONFIG_PATH.open(encoding="utf-8") as fh:
            _edi_config = json.load(fh)
        logger.info(
            "Loaded EDI routing config: %d members", len(_edi_config.get("members", []))
        )
    except Exception as exc:
        logger.error("Failed to load edi_routing.json: %s", exc)
        _edi_config = {"team": "EDI Team", "team_lead_email": "", "members": []}
    return _edi_config


class RoutingAgent(OllamaAgent):

    async def route(self, category: str, priority: str, summary: str) -> dict:
        """
        Matches keywords from data/edi_routing.json against the ticket summary
        and returns the first member whose keyword appears in the text.

        Returns:
            {
                "team": str,
                "assignee": str,
                "assignee_email": str,
                "team_lead_email": str,
            }
        """
        config = _load_edi_config()
        team = config.get("team", "EDI Team")
        team_lead_email = config.get("team_lead_email", "")

        search_text = summary.lower()

        for member in config.get("members", []):
            for keyword in member.get("keywords", []):
                if keyword.lower() in search_text:
                    return {
                        "team": team,
                        "assignee": member["name"],
                        "assignee_email": member.get("email", ""),
                        "team_lead_email": team_lead_email,
                    }

        # No keyword matched
        return {
            "team": team,
            "assignee": "Unassigned",
            "assignee_email": "",
            "team_lead_email": team_lead_email,
        }
