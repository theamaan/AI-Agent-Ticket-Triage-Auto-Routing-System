"""
Feedback Agent — persists human corrections and triggers retraining
when correction count reaches the configured threshold.
"""
from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.database.models import Feedback, Ticket

logger = logging.getLogger(__name__)


async def save_feedback(
    session: AsyncSession,
    ticket_db_id: int,
    corrected_category: str | None,
    corrected_priority: str | None,
    corrected_team: str | None,
    corrected_assignee: str | None,
    reviewer: str | None,
    notes: str | None,
) -> Feedback:
    # ── Duplicate guard: one review per ticket ────────────────────────────────
    existing_result = await session.execute(
        select(Feedback).where(Feedback.ticket_id == ticket_db_id)
    )
    if existing_result.scalar_one_or_none() is not None:
        raise ValueError(
            f"Ticket db_id={ticket_db_id} has already been reviewed. "
            "Duplicate review submissions are not allowed."
        )

    fb = Feedback(
        ticket_id=ticket_db_id,
        corrected_category=corrected_category,
        corrected_priority=corrected_priority,
        corrected_team=corrected_team,
        corrected_assignee=corrected_assignee,
        reviewer=reviewer,
        notes=notes,
    )
    session.add(fb)

    # ── Mark ticket as manually reviewed so it leaves the review queue ────────
    ticket_result = await session.execute(
        select(Ticket).where(Ticket.id == ticket_db_id)
    )
    ticket = ticket_result.scalar_one_or_none()
    if ticket is not None:
        ticket.routing_status = "Manual"
        logger.info(
            "Ticket db_id=%d routing_status updated to 'Manual' after review.",
            ticket_db_id,
        )

    await session.commit()
    await session.refresh(fb)
    logger.info("Feedback #%d saved for ticket db_id=%d", fb.id, ticket_db_id)

    # Check if retraining threshold is reached (count unique reviewed tickets)
    count_result = await session.execute(
        select(func.count(func.distinct(Feedback.ticket_id))).select_from(Feedback)
    )
    total = count_result.scalar_one()
    if total > 0 and total % settings.feedback_retrain_threshold == 0:
        logger.info(
            "Feedback threshold reached (%d unique tickets). Consider retraining — "
            "run: python src/ml/trainer.py",
            total,
        )

    return fb


async def get_feedback_count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(Feedback))
    return result.scalar_one()
