"""Unit tests for confidence agent and pipeline utilities."""
from __future__ import annotations

import pytest
from src.agents.confidence_agent import compute_confidence, decide_routing_status
from src.agents.priority_agent import _rule_based_priority
from src.pipeline.excel_pipeline import read_tickets


# ── Confidence Agent ───────────────────────────────────────────────────────────

def test_compute_confidence_all_signals():
    result = compute_confidence(ml_confidence=0.9, llm_confidence=0.8, priority_confidence=0.95)
    assert 0.85 <= result <= 0.95


def test_compute_confidence_ml_only():
    result = compute_confidence(ml_confidence=0.7, llm_confidence=None, priority_confidence=0.8)
    assert 0.0 < result < 1.0


def test_decide_routing_auto():
    assert decide_routing_status(0.92) == "Auto-Routed"


def test_decide_routing_flagged():
    assert decide_routing_status(0.72) == "Flagged"


def test_decide_routing_held():
    assert decide_routing_status(0.40) == "Held"


# ── Priority Agent (rule-based) ────────────────────────────────────────────────

def test_priority_rule_p1_outage():
    assert _rule_based_priority("production is down complete failure") == "P1"


def test_priority_rule_p2_degraded():
    assert _rule_based_priority("service is degraded for multiple users") == "P2"


def test_priority_rule_p4_cosmetic():
    assert _rule_based_priority("cosmetic issue, no business impact") == "P4"


def test_priority_rule_no_match_returns_none():
    assert _rule_based_priority("please update the user guide document") is None


# ── Excel Pipeline ─────────────────────────────────────────────────────────────

def test_read_tickets_missing_required_column():
    import pandas as pd
    import io

    df = pd.DataFrame([{"Description": "Something happened"}])
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    buf.seek(0)

    with pytest.raises(ValueError, match="missing required columns"):
        read_tickets(buf.read())


def test_read_tickets_valid():
    import pandas as pd
    import io

    df = pd.DataFrame([
        {"Ticket_ID": "TKT-00001", "Summary": "Server down", "Description": "Production server is not responding."},
        {"Ticket_ID": "TKT-00002", "Summary": "Login error", "Description": "Cannot log in to portal."},
    ])
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    buf.seek(0)

    rows = read_tickets(buf.read())
    assert len(rows) == 2
    assert rows[0]["Summary"] == "Server down"
