"""
Excel Pipeline — reads input .xlsx, validates schema, returns list of ticket dicts.
Also writes enriched output .xlsx with AI prediction columns appended.
"""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"Summary", "Description"}

OUTPUT_COLUMNS = [
    "Ticket_ID", "Date", "Summary", "Description", "Reporter",
    "Category", "Priority", "Assigned_Team", "Status",
    # AI-added columns
    "AI_Category", "AI_Priority", "Assigned_Team_AI", "Assigned_To",
    "Assignee_Email", "ML_Confidence", "LLM_Confidence", "Final_Confidence",
    "Routing_Status", "Email_Sent",
]


def read_tickets(file_bytes: bytes, filename: str = "upload.xlsx") -> list[dict]:
    """Parse uploaded Excel bytes into a list of row dicts."""
    try:
        df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
    except Exception as exc:
        raise ValueError(f"Cannot read Excel file '{filename}': {exc}") from exc

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Excel file is missing required columns: {missing}. "
            f"Found: {list(df.columns)}"
        )

    # Normalise column names
    df.columns = [str(c).strip() for c in df.columns]

    # Fill NaN with empty string for text fields
    for col in ["Summary", "Description", "Ticket_ID", "Reporter", "Date", "Status"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    # Generate Ticket_ID if missing
    if "Ticket_ID" not in df.columns or df["Ticket_ID"].str.strip().eq("").all():
        df["Ticket_ID"] = [f"TKT-{i+1:05d}" for i in range(len(df))]

    return df.to_dict("records")


def write_enriched_excel(results: list[dict]) -> bytes:
    """Serialise enriched ticket results to Excel bytes for download."""
    df = pd.DataFrame(results)

    # Reorder columns — only include those that exist in the data
    ordered = [c for c in OUTPUT_COLUMNS if c in df.columns]
    remaining = [c for c in df.columns if c not in ordered]
    df = df[ordered + remaining]

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Triage_Results")

        # Apply conditional formatting via openpyxl
        ws = writer.sheets["Triage_Results"]
        _apply_styles(ws, df)

    buf.seek(0)
    return buf.read()


def _apply_styles(ws: Any, df: pd.DataFrame) -> None:
    """Colour-code priority cells (P1=red, P2=orange, P3=blue, P4=green)."""
    try:
        from openpyxl.styles import Font, PatternFill

        priority_colours = {
            "P1": "FFC7CE",  # red
            "P2": "FFEB9C",  # orange/yellow
            "P3": "BDD7EE",  # blue
            "P4": "C6EFCE",  # green
        }

        col_names = list(df.columns)
        priority_col_idx = None
        for i, name in enumerate(col_names):
            if name in ("AI_Priority", "Priority"):
                priority_col_idx = i + 1  # 1-based
                break

        if priority_col_idx is None:
            return

        for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
            cell = ws.cell(row=row_idx, column=priority_col_idx)
            colour = priority_colours.get(str(cell.value), None)
            if colour:
                cell.fill = PatternFill(
                    start_color=colour, end_color=colour, fill_type="solid"
                )
    except Exception as exc:
        logger.debug("Could not apply Excel styles: %s", exc)
