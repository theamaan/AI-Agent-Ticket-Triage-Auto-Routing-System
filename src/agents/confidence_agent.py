"""
Confidence Agent — aggregates signals into a final confidence score
and decides routing action (Auto-Route / Flag / Hold).
"""
from __future__ import annotations

from src.config.settings import settings


def compute_confidence(
    ml_confidence: float | None,
    llm_confidence: float | None,
    priority_confidence: float,
) -> float:
    """
    Compute a weighted confidence score based on which classifier was used.

    Two paths:

    Path A — LLM was used as the primary/fallback classifier
    (llm_confidence is not None):
        The ML score that triggered the LLM fallback was already below the
        reliability threshold.  Including that low score at 50% weight would
        overwhelm the LLM's confident answer.  Exclude it entirely and give
        the LLM the dominant weight.
            score = llm_confidence × 0.70 + priority_confidence × 0.30

    Path B — ML model was used alone (llm_confidence is None):
        ML prediction was strong enough (≥ 0.55).  Give ML the dominant weight.
            score = ml_confidence × 0.80 + priority_confidence × 0.20

    Example (why the old formula failed):
        ml=0.35 (below threshold, LLM fallback), llm=0.70, priority=0.92
        OLD: (0.35×0.5 + 0.70×0.3 + 0.92×0.2) / 1.0 = 0.569  → Flagged
        NEW: 0.70×0.70 + 0.92×0.30               = 0.766  → Auto-Routed ✅
    """
    if llm_confidence is not None:
        # Path A: LLM was the effective classifier
        return round(llm_confidence * 0.70 + priority_confidence * 0.30, 4)

    if ml_confidence is not None:
        # Path B: ML was the sole classifier
        return round(ml_confidence * 0.80 + priority_confidence * 0.20, 4)

    # No signals at all — neutral score
    return 0.50


def decide_routing_status(confidence: float) -> str:
    """
    Apply configured thresholds:
      ≥ CONFIDENCE_AUTO_ROUTE  → "Auto-Routed"
      ≥ CONFIDENCE_FLAG        → "Flagged"
      else                     → "Held"
    """
    if confidence >= settings.confidence_auto_route:
        return "Auto-Routed"
    if confidence >= settings.confidence_flag:
        return "Flagged"
    return "Held"
