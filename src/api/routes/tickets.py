"""Ticket routes — upload Excel, list, retrieve."""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from src.database.models import Ticket
from src.pipeline.excel_pipeline import read_tickets, write_enriched_excel
from src.pipeline.orchestrator import Orchestrator

router = APIRouter()
logger = logging.getLogger(__name__)

_orchestrator = Orchestrator()


@router.post("/process")
async def process_tickets(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    """
    Upload an Excel file (.xlsx) of tickets.
    Returns an enriched Excel file with AI predictions as a download.
    """
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are accepted.")

    raw_bytes = await file.read()
    if len(raw_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        tickets_in = read_tickets(raw_bytes, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if not tickets_in:
        raise HTTPException(status_code=422, detail="No rows found in the uploaded file.")

    results = await _orchestrator.process_batch(tickets_in)
    await _orchestrator.persist_results(session, results)

    enriched_bytes = write_enriched_excel(results)

    summary = {
        "total": len(results),
        "auto_routed": sum(1 for r in results if r.get("Routing_Status") == "Auto-Routed"),
        "flagged": sum(1 for r in results if r.get("Routing_Status") == "Flagged"),
        "held": sum(1 for r in results if r.get("Routing_Status") == "Held"),
    }
    logger.info("Processed batch of %d tickets: %s", len(results), summary)

    return Response(
        content=enriched_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=triage_results.xlsx"},
    )


@router.get("")
async def list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    routing_status: str | None = Query(None),
    team: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """List processed tickets with optional filters and pagination."""
    stmt = select(Ticket).order_by(Ticket.created_at.desc())

    if routing_status:
        stmt = stmt.where(Ticket.routing_status == routing_status)
    if team:
        stmt = stmt.where(Ticket.assigned_team == team)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    rows = (await session.execute(stmt)).scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_ticket_to_dict(t) for t in rows],
    }


@router.get("/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Retrieve a single ticket by Ticket_ID."""
    result = await session.execute(
        select(Ticket).where(Ticket.ticket_id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")
    return _ticket_to_dict(ticket)


def _ticket_to_dict(t: Ticket) -> dict:
    return {
        "id": t.id,
        "ticket_id": t.ticket_id,
        "date": t.date,
        "summary": t.summary,
        "description": t.description,
        "reporter": t.reporter,
        "original_category": t.original_category,
        "original_priority": t.original_priority,
        "ai_category": t.ai_category,
        "ai_priority": t.ai_priority,
        "assigned_team": t.assigned_team,
        "assigned_to": t.assigned_to,
        "assignee_email": t.assignee_email,
        "ml_confidence": t.ml_confidence,
        "llm_confidence": t.llm_confidence,
        "final_confidence": t.final_confidence,
        "routing_status": t.routing_status,
        "email_sent": t.email_sent,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "processed_at": t.processed_at.isoformat() if t.processed_at else None,
    }
