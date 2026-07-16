"""
Approval routes — handles the one-click approve links sent in recommendation emails.

GET /api/approve/{ticket_id}?token=<approval_token>
  → marks the ticket as Approved and returns a confirmation HTML page.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from src.database.models import Ticket

router = APIRouter()
logger = logging.getLogger(__name__)

_STYLE = "font-family:Calibri,Arial,sans-serif;text-align:center;padding:60px;color:#1a1a2e"


@router.get("/{ticket_id}", response_class=HTMLResponse, tags=["Approvals"])
async def approve_ticket(
    ticket_id: str,
    token: str,
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    """
    Called when the approver clicks an Approve button in the recommendation email.
    Validates the one-time token, flips routing_status to 'Approved', and returns
    a simple confirmation page.
    """
    result = await session.execute(
        select(Ticket).where(Ticket.ticket_id == ticket_id)
    )
    ticket = result.scalar_one_or_none()

    # ── Invalid token or ticket not found ─────────────────────────────────────
    if not ticket or ticket.approval_token != token:
        logger.warning("Invalid approval attempt for ticket_id=%s", ticket_id)
        return HTMLResponse(
            f"""
            <html><body style='{_STYLE}'>
              <h1 style='color:#f5222d'>&#10060; Invalid Link</h1>
              <p>This approval link is invalid or has already been used.</p>
              <p style='color:#8c8c8c;font-size:13px'>Ticket: {ticket_id}</p>
            </body></html>""",
            status_code=400,
        )

    # ── Already approved ──────────────────────────────────────────────────────
    if ticket.routing_status == "Approved":
        return HTMLResponse(
            f"""
            <html><body style='{_STYLE}'>
              <h1 style='color:#1677ff'>&#8505; Already Approved</h1>
              <p>Ticket <b>{ticket_id}</b> was already approved as
                 <b>{ticket.assigned_team}</b>.</p>
            </body></html>""",
        )

    # ── Approve ───────────────────────────────────────────────────────────────
    ticket.routing_status = "Approved"
    await session.commit()
    logger.info("Ticket %s approved → %s", ticket_id, ticket.assigned_team)

    return HTMLResponse(
        f"""
        <html><body style='{_STYLE}'>
          <div style='max-width:520px;margin:auto;background:#f6ffed;
                      border:1px solid #b7eb8f;border-radius:8px;padding:40px'>
            <h1 style='color:#52c41a;font-size:48px;margin:0'>&#10003;</h1>
            <h2 style='color:#237804'>Approved!</h2>
            <p>Ticket <b>{ticket_id}</b> has been confirmed as routed to:</p>
            <p style='font-size:22px;font-weight:700;color:#001529'>
              {ticket.assigned_team}
            </p>
            <p style='color:#8c8c8c;font-size:13px;margin-top:24px'>
              You can close this tab.<br>
              Download the final Excel once all tickets are approved.
            </p>
          </div>
        </body></html>""",
    )
