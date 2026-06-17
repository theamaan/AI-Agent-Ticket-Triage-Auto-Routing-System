"""
Priority Agent — assigns P1–P4 priority.
Rule-based fast path for obvious keywords; Ollama for ambiguous cases.
"""
from __future__ import annotations

import logging
import re

from src.agents.base_agent import OllamaAgent

logger = logging.getLogger(__name__)

# Keyword rules: checked in priority order (P1 first)
_PRIORITY_RULES: list[tuple[str, list[str]]] = [
    ("P1", [
        "down", "outage", "production down", "critical", "sev1", "severity 1",
        "system unavailable", "data loss", "breach", "malware", "ransomware",
        "complete failure", "all users affected",
    ]),
    ("P2", [
        "degraded", "slow", "intermittent", "partial outage", "high impact",
        "workaround not available", "multiple users affected", "sev2",
    ]),
    ("P4", [
        "cosmetic", "minor", "low priority", "nice to have", "enhancement",
        "documentation", "sev4", "no business impact",
    ]),
]


def _rule_based_priority(text: str) -> str | None:
    lower = text.lower()
    for priority, keywords in _PRIORITY_RULES:
        if any(kw in lower for kw in keywords):
            return priority
    return None  # P3 is default; let LLM confirm ambiguous cases


class PriorityAgent(OllamaAgent):

    async def assign_priority(self, summary: str, description: str) -> dict:
        """
        Returns:
            {
                "priority": "P1" | "P2" | "P3" | "P4",
                "priority_confidence": float,
                "priority_reasoning": str,
                "source": "rules" | "llm"
            }
        """
        text = f"{summary} {description}"
        rule_priority = _rule_based_priority(text)

        if rule_priority:
            return {
                "priority": rule_priority,
                "priority_confidence": 0.92,
                "priority_reasoning": "Matched keyword rule.",
                "source": "rules",
            }

        # Ambiguous — ask LLM
        result = await self._llm_priority(summary, description)
        priority = result.get("priority", "P3")
        if priority not in ("P1", "P2", "P3", "P4"):
            priority = "P3"

        return {
            "priority": priority,
            "priority_confidence": float(result.get("confidence", 0.6)),
            "priority_reasoning": result.get("reasoning", "LLM assessment."),
            "source": "llm",
        }

    async def _llm_priority(self, summary: str, description: str) -> dict:
        prompt = (
            "You are an ITSM priority classification expert.\n\n"
            f"Ticket Summary: {summary}\n"
            f"Description: {description}\n\n"
            "Assign one priority level:\n"
            "  P1 — Critical: Production down, data loss, security breach. SLA: 1 hour.\n"
            "  P2 — High: Major functionality impaired, many users affected. SLA: 4 hours.\n"
            "  P3 — Medium: Limited impact, workaround exists. SLA: 24 hours.\n"
            "  P4 — Low: Minor issue, cosmetic, enhancement. SLA: 72 hours.\n\n"
            "Return JSON with keys: priority (P1/P2/P3/P4), confidence (0.0-1.0), reasoning (one sentence)."
            f"{self._build_json_instruction()}"
        )
        raw = await self._call_ollama(prompt)
        return self._parse_json_response(
            raw, {"priority": "P3", "confidence": 0.5, "reasoning": "Default P3."}
        )
