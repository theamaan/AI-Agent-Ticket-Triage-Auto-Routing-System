"""
Orchestrator — coordinates all agents for a batch of tickets.
Flow: ingest → classify → prioritize → route → confidence → persist → notify
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.classifier_agent import ClassifierAgent
from src.agents.confidence_agent import compute_confidence, decide_routing_status
from src.agents.priority_agent import PriorityAgent
from src.agents.routing_agent import RoutingAgent
from src.database.models import Ticket
from src.notifications import email_service

logger = logging.getLogger(__name__)


class Orchestrator:

    def __init__(self) -> None:
        self._classifier = ClassifierAgent()
        self._priority_agent = PriorityAgent()
        self._routing_agent = RoutingAgent()

    async def process_ticket(self, raw: dict) -> dict:
        """Process a single ticket dict through the full agent pipeline."""
        summary = str(raw.get("Summary", ""))
        description = str(raw.get("Description", ""))
        ticket_id = str(raw.get("Ticket_ID", "UNKNOWN"))

        logger.info("Processing ticket: %s", ticket_id)

        # ── Agent calls (classifier + priority can run concurrently) ──────────
        classification, priority_result = await asyncio.gather(
            self._classifier.classify(summary, description),
            self._priority_agent.assign_priority(summary, description),
        )

        category = classification["category"]
        priority = priority_result["priority"]

        # ── Routing ───────────────────────────────────────────────────────────
        routing = await self._routing_agent.route(category, priority, summary)

        # ── Confidence aggregation ────────────────────────────────────────────
        final_confidence = compute_confidence(
            ml_confidence=classification.get("ml_confidence"),
            llm_confidence=classification.get("llm_confidence"),
            priority_confidence=priority_result["priority_confidence"],
        )
        routing_status = decide_routing_status(final_confidence)

        result: dict[str, Any] = {
            **raw,
            "AI_Category": category,
            "AI_Priority": priority,
            "Assigned_Team_AI": routing["team"],
            "Assigned_To": routing["assignee"],
            "Assignee_Email": routing["assignee_email"],
            "Team_Lead_Email": routing["team_lead_email"],
            "ML_Confidence": classification.get("ml_confidence"),
            "LLM_Confidence": classification.get("llm_confidence"),
            "Final_Confidence": final_confidence,
            "Routing_Status": routing_status,
            "Email_Sent": False,
            "processed_at": datetime.utcnow().isoformat(),
        }

        # ── Email notification (only for auto-routed) ─────────────────────────
        if routing_status == "Auto-Routed" and routing["assignee_email"]:
            sent = email_service.send_auto_route_notification(
                to_email=routing["assignee_email"],
                ticket_id=ticket_id,
                summary=summary,
                category=category,
                priority=priority,
                assignee=routing["assignee"],
                team=routing["team"],
                confidence=final_confidence,
            )
            result["Email_Sent"] = sent

        return result

    async def process_batch(self, tickets: list[dict]) -> list[dict]:
        """Process a list of tickets; returns enriched list."""
        results = []
        for ticket in tickets:
            try:
                enriched = await self.process_ticket(ticket)
                results.append(enriched)
            except Exception as exc:
                logger.error("Failed to process ticket %s: %s", ticket.get("Ticket_ID"), exc)
                results.append({**ticket, "Routing_Status": "Error", "Email_Sent": False})

        # Send flagged digest if any flagged/held tickets
        flagged = [r for r in results if r.get("Routing_Status") in ("Flagged", "Held")]
        if flagged:
            # Send digest to first team lead email found
            lead_emails = {r.get("Team_Lead_Email") for r in flagged if r.get("Team_Lead_Email")}
            for lead_email in lead_emails:
                email_service.send_flagged_digest(lead_email, flagged)

        return results

    async def persist_results(
        self,
        session: AsyncSession,
        results: list[dict],
    ) -> list[Ticket]:
        """Save enriched ticket results to the database."""
        db_tickets = []
        for r in results:
            ticket = Ticket(
                ticket_id=r.get("Ticket_ID", ""),
                date=str(r.get("Date", "")),
                summary=r.get("Summary", ""),
                description=r.get("Description", ""),
                reporter=r.get("Reporter"),
                original_category=r.get("Category"),
                original_priority=r.get("Priority"),
                original_team=r.get("Assigned_Team"),
                ai_category=r.get("AI_Category"),
                ai_priority=r.get("AI_Priority"),
                assigned_team=r.get("Assigned_Team_AI"),
                assigned_to=r.get("Assigned_To"),
                assignee_email=r.get("Assignee_Email"),
                ml_confidence=r.get("ML_Confidence"),
                llm_confidence=r.get("LLM_Confidence"),
                final_confidence=r.get("Final_Confidence"),
                routing_status=r.get("Routing_Status"),
                email_sent=bool(r.get("Email_Sent", False)),
                processed_at=datetime.utcnow(),
            )
            session.add(ticket)
            db_tickets.append(ticket)

        await session.commit()
        return db_tickets
