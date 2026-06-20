from __future__ import annotations

import os
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Ollama ────────────────────────────────────────────────────────────────
    ollama_enabled: bool = True
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gpt-oss:120b-cloud"
    ollama_timeout: int = 120

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./tickets.db"

    # ── Email ─────────────────────────────────────────────────────────────────
    email_enabled: bool = True
    email_username: str = ""
    email_password: str = ""
    email_from_name: str = "Ticket Triage System"
    email_smtp_host: str = "smtp.gmail.com"
    email_smtp_port: int = 587

    # ── Routing ───────────────────────────────────────────────────────────────
    routing_config_path: str = "data/routing_config.xlsx"

    # ── Confidence Thresholds ────────────────────────────────────────────────
    # Lowered from 0.85/0.65 to reflect realistic scores from a small training set.
    # With 50 training samples the weighted confidence rarely exceeds 0.85.
    # Raise these values (via .env) as the model improves with more feedback data.
    #   CONFIDENCE_AUTO_ROUTE=0.85  ← restore once accuracy >= 90%
    #   CONFIDENCE_FLAG=0.65        ← restore once accuracy >= 90%
    confidence_auto_route: float = 0.72
    confidence_flag: float = 0.55

    # ── ML Model Paths ────────────────────────────────────────────────────────
    ml_model_path: str = "src/ml/models/classifier.pkl"
    ml_vectorizer_path: str = "src/ml/models/vectorizer.pkl"
    training_data_path: str = "data/sample_tickets.xlsx"

    # ── API ───────────────────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # ── Feedback ──────────────────────────────────────────────────────────────
    feedback_retrain_threshold: int = 20

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


settings = Settings()
