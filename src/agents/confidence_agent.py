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
    Weighted average of available confidence signals.
    Weights: ML=0.5, LLM=0.3, Priority=0.2
    Falls back gracefully if any signal is unavailable.
    """
    scores: list[tuple[float, float]] = []

    if ml_confidence is not None:
        scores.append((ml_confidence, 0.5))
    if llm_confidence is not None:
        scores.append((llm_confidence, 0.3))
    scores.append((priority_confidence, 0.2))

    total_weight = sum(w for _, w in scores)
    if total_weight == 0:
        return 0.5

    weighted_sum = sum(v * w for v, w in scores)
    return round(weighted_sum / total_weight, 4)


def decide_routing_status(confidence: float) -> str:
    """
    Apply configured thresholds:
      > CONFIDENCE_AUTO_ROUTE  → "Auto-Routed"
      > CONFIDENCE_FLAG        → "Flagged"
      else                     → "Held"
    """
    if confidence >= settings.confidence_auto_route:
        return "Auto-Routed"
    if confidence >= settings.confidence_flag:
        return "Flagged"
    return "Held"
