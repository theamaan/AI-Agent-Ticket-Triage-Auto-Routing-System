"""
Folder Runner — processes every .xlsx in the input/ folder through the full
agent pipeline and writes enriched output files to the output/ folder.

Called automatically on API startup (lifespan) and via POST /api/run.
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path

from src.database.connection import get_session_factory
from src.pipeline.excel_pipeline import read_tickets, write_enriched_excel
from src.pipeline.orchestrator import Orchestrator

logger = logging.getLogger(__name__)

INPUT_DIR     = Path("input")
PROCESSED_DIR = Path("input") / "processed"
OUTPUT_DIR    = Path("output")

_orchestrator = Orchestrator()


async def run_folder() -> dict:
    """
    Scan INPUT_DIR for .xlsx files, run each through the pipeline, write an
    enriched Excel file to OUTPUT_DIR, then move the original to PROCESSED_DIR.

    Returns a summary dict suitable for JSON responses or logging.
    """
    # Ensure the three directories always exist
    INPUT_DIR.mkdir(exist_ok=True)
    PROCESSED_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    xlsx_files = sorted(INPUT_DIR.glob("*.xlsx"))

    if not xlsx_files:
        logger.info("Folder runner: no .xlsx files found in '%s'.", INPUT_DIR.resolve())
        return {"processed_count": 0, "files": []}

    session_factory = get_session_factory()
    file_summaries: list[dict] = []

    for file_path in xlsx_files:
        logger.info("Folder runner: starting '%s'", file_path.name)
        try:
            # 1. Read
            tickets_in = read_tickets(file_path.read_bytes(), file_path.name)

            # 2. Run agents
            results = await _orchestrator.process_batch(tickets_in)

            # 3. Persist to database
            async with session_factory() as session:
                await _orchestrator.persist_results(session, results)

            # 4. Write enriched Excel to output/
            out_path = OUTPUT_DIR / f"enriched_{file_path.name}"
            out_path.write_bytes(write_enriched_excel(results))

            # 5. Move original to input/processed/
            shutil.move(str(file_path), str(PROCESSED_DIR / file_path.name))

            summary = {
                "file": file_path.name,
                "output": out_path.name,
                "total": len(results),
                "auto_routed": sum(1 for r in results if r.get("Routing_Status") == "Auto-Routed"),
                "flagged":     sum(1 for r in results if r.get("Routing_Status") == "Flagged"),
                "held":        sum(1 for r in results if r.get("Routing_Status") == "Held"),
                "status": "ok",
            }
            logger.info(
                "Folder runner: finished '%s' → '%s' | total=%d auto=%d flagged=%d held=%d",
                file_path.name, out_path.name,
                summary["total"], summary["auto_routed"],
                summary["flagged"], summary["held"],
            )

        except Exception as exc:
            logger.error("Folder runner: failed on '%s': %s", file_path.name, exc)
            summary = {"file": file_path.name, "status": "error", "error": str(exc)}

        file_summaries.append(summary)

    return {"processed_count": len(xlsx_files), "files": file_summaries}
