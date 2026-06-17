"""
Classifier Agent — predicts ticket category.
Primary: scikit-learn ML model (fast, offline).
Fallback: Ollama LLM when ML confidence < threshold or model unavailable.
"""
from __future__ import annotations

import logging

from src.agents.base_agent import OllamaAgent
from src.ml import model_loader

logger = logging.getLogger(__name__)

VALID_CATEGORIES = [
    "Test case failure", "Regression test blocked", "UAT environment issue",
    "Automation script error", "Test data missing", "QA sign-off pending",
    "Performance test failure",
    "EDI transaction error", "835 file not received", "837 claim rejection",
    "EDI partner connectivity", "HIPAA validation failure", "EDI mapping issue",
    "Acknowledgement not received", "Trading partner setup",
    "BizTalk orchestration failure", "Message routing error",
    "BizTalk pipeline exception", "Suspended message in BizTalk",
    "BizTalk adapter configuration", "Schema validation error",
    "BizTalk host instance down", "Tracking database issue",
    "Database connection timeout", "Slow query performance", "Deadlock detected",
    "Backup job failure", "Data integrity issue", "Stored procedure error",
    "Database migration failure", "Disk space alert on DB server",
    "Index rebuild needed", "Replication lag",
    "VPN connectivity issue", "Network latency spike",
    "Firewall rule blocking traffic", "DNS resolution failure",
    "Load balancer misconfiguration",
    "User account locked", "Password reset request",
    "Permission denied on folder", "MFA not working", "New user onboarding access",
    "Suspicious login attempt", "Malware detected on endpoint",
    "Phishing email reported", "Security patch deployment",
    "Compliance audit finding",
]

# Threshold below which we call the LLM for a second opinion
ML_CONFIDENCE_THRESHOLD = 0.55


class ClassifierAgent(OllamaAgent):

    async def classify(self, summary: str, description: str) -> dict:
        """
        Returns:
            {
                "category": str,
                "ml_confidence": float,
                "llm_confidence": float | None,
                "source": "ml" | "llm" | "ml+llm"
            }
        """
        text = f"{summary} {description}".strip()

        ml_category: str | None = None
        ml_confidence: float = 0.0

        # ── ML prediction ─────────────────────────────────────────────────────
        if model_loader.is_model_available():
            try:
                ml_category, ml_confidence = model_loader.predict(text)
            except Exception as exc:
                logger.warning("ML prediction failed: %s", exc)

        # ── LLM fallback ──────────────────────────────────────────────────────
        if not ml_category or ml_confidence < ML_CONFIDENCE_THRESHOLD:
            llm_result = await self._llm_classify(summary, description)
            llm_category = llm_result.get("category", ml_category or "Unknown")
            llm_confidence = float(llm_result.get("confidence", 0.5))

            return {
                "category": llm_category,
                "ml_confidence": ml_confidence,
                "llm_confidence": llm_confidence,
                "source": "ml+llm" if ml_category else "llm",
            }

        return {
            "category": ml_category,
            "ml_confidence": ml_confidence,
            "llm_confidence": None,
            "source": "ml",
        }

    async def _llm_classify(self, summary: str, description: str) -> dict:
        categories_str = "\n".join(f"  - {c}" for c in VALID_CATEGORIES)
        prompt = (
            f"You are an IT support ticket classifier.\n\n"
            f"Ticket Summary: {summary}\n"
            f"Ticket Description: {description}\n\n"
            f"Choose the single best category from this list:\n{categories_str}\n\n"
            f"Return JSON with keys: category (exact match from list), confidence (0.0-1.0)."
            f"{self._build_json_instruction()}"
        )
        raw = await self._call_ollama(prompt)
        return self._parse_json_response(
            raw, {"category": "Unknown", "confidence": 0.3}
        )
