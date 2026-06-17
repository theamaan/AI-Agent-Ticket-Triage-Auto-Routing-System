"""
Singleton loader for the trained sklearn pipeline.
Lazy-loads on first call; thread-safe for async FastAPI usage.
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional

import joblib
from sklearn.pipeline import Pipeline

from src.config.settings import settings
from src.ml.evaluator import get_prediction_with_confidence

_lock = threading.Lock()
_model: Optional[Pipeline] = None


def load_model() -> Pipeline:
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                path = settings.ml_model_path
                if not Path(path).exists():
                    raise FileNotFoundError(
                        f"ML model not found at '{path}'. "
                        "Run: python src/ml/trainer.py"
                    )
                _model = joblib.load(path)
    return _model


def predict(text: str) -> tuple[str, float]:
    """Return (category, confidence) using the loaded sklearn pipeline."""
    model = load_model()
    return get_prediction_with_confidence(model, text)


def is_model_available() -> bool:
    return Path(settings.ml_model_path).exists()
