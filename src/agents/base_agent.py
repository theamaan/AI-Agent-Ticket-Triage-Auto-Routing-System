"""
Base Ollama agent — HTTP client, prompt builder, JSON response parser.
All agents inherit from this class.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from src.config.settings import settings

logger = logging.getLogger(__name__)


class OllamaAgent:
    """Thin async wrapper around the Ollama /api/generate endpoint."""

    def __init__(self) -> None:
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_model
        self._enabled = settings.ollama_enabled
        self._timeout = settings.ollama_timeout

    async def _call_ollama(self, prompt: str) -> str:
        """Send prompt to Ollama and return the raw text response."""
        if not self._enabled:
            return ""

        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,   # Low temperature for deterministic classification
                "top_p": 0.9,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base_url}/api/generate",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", "").strip()
        except httpx.TimeoutException:
            logger.warning("Ollama request timed out after %ss", self._timeout)
            return ""
        except httpx.HTTPError as exc:
            logger.warning("Ollama HTTP error: %s", exc)
            return ""
        except Exception as exc:
            logger.error("Unexpected Ollama error: %s", exc)
            return ""

    def _parse_json_response(self, raw: str, fallback: dict) -> dict:
        """Extract the first JSON object from a model response."""
        if not raw:
            return fallback
        # Try direct parse
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        # Find JSON block inside backtick fences or prose
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(raw[start:end])
            except json.JSONDecodeError:
                pass
        logger.debug("Could not parse JSON from Ollama response: %s", raw[:200])
        return fallback

    def _build_json_instruction(self) -> str:
        return (
            "\nRespond ONLY with a valid JSON object. "
            "Do not include any explanation, markdown fences, or extra text."
        )
