"""KPI metrics route."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from src.database.models import Feedback, ModelMetrics, Ticket

router = APIRouter()


@router.get("/kpi")
async def get_kpi(session: AsyncSession = Depends(get_session)):
    """Return KPI metrics for the dashboard."""
    total_result = await session.execute(select(func.count()).select_from(Ticket))
    total_tickets = total_result.scalar_one()

    auto_result = await session.execute(
        select(func.count()).where(Ticket.routing_status == "Auto-Routed")
    )
    auto_routed = auto_result.scalar_one()

    # Flagged = tickets currently pending review (excludes reviewed/Manual tickets)
    flagged_result = await session.execute(
        select(func.count()).where(Ticket.routing_status == "Flagged")
    )
    flagged = flagged_result.scalar_one()

    held_result = await session.execute(
        select(func.count()).where(Ticket.routing_status == "Held")
    )
    held = held_result.scalar_one()

    # Human corrections = count of UNIQUE tickets that received a correction
    # (prevents duplicate reviews inflating the count)
    feedback_result = await session.execute(
        select(func.count(func.distinct(Feedback.ticket_id))).select_from(Feedback)
    )
    total_feedback = feedback_result.scalar_one()

    avg_conf_result = await session.execute(
        select(func.avg(Ticket.final_confidence)).where(
            Ticket.final_confidence.isnot(None)
        )
    )
    avg_confidence = avg_conf_result.scalar_one() or 0.0

    # Team distribution
    team_dist_result = await session.execute(
        select(Ticket.assigned_team, func.count().label("count"))
        .where(Ticket.assigned_team.isnot(None))
        .group_by(Ticket.assigned_team)
        .order_by(func.count().desc())
    )
    team_distribution = [
        {"team": row[0], "count": row[1]} for row in team_dist_result.all()
    ]

    # Priority distribution
    priority_dist_result = await session.execute(
        select(Ticket.ai_priority, func.count().label("count"))
        .where(Ticket.ai_priority.isnot(None))
        .group_by(Ticket.ai_priority)
        .order_by(Ticket.ai_priority)
    )
    priority_distribution = [
        {"priority": row[0], "count": row[1]} for row in priority_dist_result.all()
    ]

    # Latest model metrics
    metrics_result = await session.execute(
        select(ModelMetrics).order_by(ModelMetrics.recorded_at.desc()).limit(1)
    )
    latest_model = metrics_result.scalar_one_or_none()

    auto_route_pct = round((auto_routed / total_tickets * 100), 1) if total_tickets > 0 else 0.0

    return {
        "total_tickets": total_tickets,
        "auto_routed": auto_routed,
        "auto_route_pct": auto_route_pct,
        "flagged": flagged,
        "held": held,
        "total_feedback": total_feedback,
        "avg_confidence": round(avg_confidence, 4),
        "team_distribution": team_distribution,
        "priority_distribution": priority_distribution,
        "model_accuracy": latest_model.accuracy if latest_model else None,
        "model_f1_macro": latest_model.f1_macro if latest_model else None,
        "model_version": latest_model.model_version if latest_model else "Not trained",
    }
