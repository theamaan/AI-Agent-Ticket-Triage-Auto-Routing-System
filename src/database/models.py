from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class RoutingStatus(str, enum.Enum):
    AUTO_ROUTED = "Auto-Routed"
    FLAGGED = "Flagged"
    HELD = "Held"
    MANUAL = "Manual"


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    date: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    summary: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    reporter: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Original fields
    original_category: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    original_priority: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    original_team: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # AI predictions
    ai_category: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    ai_priority: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    assigned_team: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    assignee_email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Confidence
    ml_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    llm_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    final_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    routing_status: Mapped[Optional[str]] = mapped_column(
        Enum(RoutingStatus), nullable=True
    )

    # Notifications
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    feedbacks: Mapped[list["Feedback"]] = relationship(
        "Feedback", back_populates="ticket", cascade="all, delete-orphan"
    )


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False)

    corrected_category: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    corrected_priority: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    corrected_team: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    corrected_assignee: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    reviewer: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="feedbacks")


class ModelMetrics(Base):
    __tablename__ = "model_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    model_version: Mapped[str] = mapped_column(String(50))
    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    f1_macro: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    training_samples: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
