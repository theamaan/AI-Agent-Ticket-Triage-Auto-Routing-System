"""FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import make_asgi_app

from src.database.connection import get_session as get_db
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.database.connection import init_db
from src.api.routes import tickets, feedback, metrics, approvals
from src.pipeline.folder_runner import run_folder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initialising database …")
    await init_db()
    logger.info("Database ready.")
    logger.info("Scanning input/ folder for Excel files …")
    await run_folder()
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="AI Ticket Triage API",
    version="1.0.0",
    description="AI Agent–based ticket triage and auto-routing system.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/prometheus-metrics", metrics_app)

# Routers
app.include_router(tickets.router,   prefix="/tickets",    tags=["Tickets"])
app.include_router(feedback.router,  prefix="/feedback",   tags=["Feedback"])
app.include_router(metrics.router,   prefix="/metrics",    tags=["Metrics"])
app.include_router(approvals.router, prefix="/api/approve", tags=["Approvals"])


@app.get("/health", tags=["Health"])
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/run", tags=["Folder Runner"])
async def run_now() -> JSONResponse:
    """
    Manually trigger the folder runner.
    Processes all .xlsx files currently in the input/ folder,
    writes enriched results to output/, and moves originals to input/processed/.
    """
    result = await run_folder()
    return JSONResponse(content=result)


@app.get("/api/tickets/download/final", tags=["Tickets"])
async def download_final_excel(
    session: AsyncSession = Depends(get_db),
) -> Response:
    """
    Generate and download the final Excel containing:
    - All EDI Team tickets  (Auto-Routed / Flagged / Held / Manual)
    - Non-EDI tickets that have been Approved by the approver
    Recommendation-pending tickets are excluded until approved.
    """
    from sqlalchemy import select as sa_select
    from src.database.models import Ticket as TicketModel
    from src.pipeline.excel_pipeline import write_enriched_excel

    res = await session.execute(sa_select(TicketModel).order_by(TicketModel.created_at))
    db_tickets = res.scalars().all()

    INCLUDE_STATUSES = {"Auto-Routed", "Flagged", "Held", "Manual", "Approved"}
    results = [
        {
            "Ticket_ID":       t.ticket_id,
            "Date":            t.date,
            "Summary":         t.summary,
            "Description":     t.description,
            "Reporter":        t.reporter,
            "Category":        t.original_category,
            "AI_Category":     t.ai_category,
            "Priority":        t.original_priority,
            "AI_Priority":     t.ai_priority,
            "Assigned_Team":   t.original_team,
            "Assigned_Team_AI": t.assigned_team,
            "Assigned_To":     t.assigned_to,
            "Assignee_Email":  t.assignee_email,
            "ML_Confidence":   t.ml_confidence,
            "LLM_Confidence":  t.llm_confidence,
            "Final_Confidence": t.final_confidence,
            "Routing_Status":  t.routing_status,
            "Email_Sent":      t.email_sent,
        }
        for t in db_tickets
        if t.routing_status in INCLUDE_STATUSES
    ]

    excel_bytes = write_enriched_excel(results)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=final_triage_results.xlsx"},
    )
