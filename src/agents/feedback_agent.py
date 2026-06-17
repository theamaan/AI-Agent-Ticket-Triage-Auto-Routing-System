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
    await session.commit()
    await session.refresh(fb)
    logger.info("Feedback #%d saved for ticket db_id=%d", fb.id, ticket_db_id)

    # Check if retraining threshold is reached
    count_result = await session.execute(select(func.count()).select_from(Feedback))
    total = count_result.scalar_one()
    if total > 0 and total % settings.feedback_retrain_threshold == 0:
        logger.info(
            "Feedback threshold reached (%d). Consider retraining — "
            "run: python src/ml/trainer.py",
            total,
        )

    return fb


async def get_feedback_count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(Feedback))
    return result.scalar_one()
