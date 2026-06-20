"""Feedback routes — submit human corrections."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.feedback_agent import save_feedback
from src.database.connection import get_session
from src.database.models import Ticket

router = APIRouter()


class FeedbackRequest(BaseModel):
    ticket_id: str
    corrected_category: str | None = None
    corrected_priority: str | None = None
    corrected_team: str | None = None
    corrected_assignee: str | None = None
    reviewer: str | None = None
    notes: str | None = None


@router.post("")
async def submit_feedback(
    body: FeedbackRequest,
    session: AsyncSession = Depends(get_session),
):
    """Submit a human correction for a processed ticket."""
    result = await session.execute(
        select(Ticket).where(Ticket.ticket_id == body.ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket '{body.ticket_id}' not found.")

    try:
        fb = await save_feedback(
            session=session,
            ticket_db_id=ticket.id,
            corrected_category=body.corrected_category,
            corrected_priority=body.corrected_priority,
            corrected_team=body.corrected_team,
            corrected_assignee=body.corrected_assignee,
            reviewer=body.reviewer,
            notes=body.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return {"message": "Feedback saved.", "feedback_id": fb.id}
