"""FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from src.config.settings import settings
from src.database.connection import init_db
from src.api.routes import tickets, feedback, metrics

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
app.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
app.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])
app.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])


@app.get("/health", tags=["Health"])
async def health() -> dict:
    return {"status": "ok"}
