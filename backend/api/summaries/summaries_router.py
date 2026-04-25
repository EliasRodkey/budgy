#!python3
"""
backend.api.summaries.summaries_router

Endpoints for reading monthly summaries and managing the dirty-months recompute queue.
"""
# Standard library imports
from pleasant_loggers import get_logger
from datetime import datetime

# Third party imports
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

# Custom imports
from pleasant_database import DatabaseFile

# Local imports
from backend.database_modules.db_session import DatabaseSession
from backend.utils.api_utils import RouterPrefixes
from backend.utils.file_utils import EDirectories

logger = get_logger(__name__)

router = APIRouter(prefix=RouterPrefixes.SUMMARIES.value, tags=["Summaries"])


# ─── Response models ──────────────────────────────────────────────────────────

class DirtyMonth(BaseModel):
    month: int
    year: int


class DirtyStatusResponse(BaseModel):
    dirty: bool
    months: list[DirtyMonth]


class RecomputeResponse(BaseModel):
    recomputed: list[DirtyMonth]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _recompute_dirty_months(dirty_months: list[tuple[int, int]]) -> list[DirtyMonth]:
    """Recomputes summaries for each dirty month and clears them from the queue."""
    db_file = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)
    recomputed = []
    with DatabaseSession(db_file) as session:
        for month, year in dirty_months:
            summary_df = session.transactions.generate_monthly_summary(month, year)
            if summary_df.empty:
                session.dirty_months.clear(month, year)
                continue
            session.summaries.upsert_summary(month, year, summary_df)
            session.dirty_months.clear(month, year)
            recomputed.append(DirtyMonth(month=month, year=year))
    return recomputed


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/dirty", response_model=DirtyStatusResponse)
async def get_dirty_status() -> DirtyStatusResponse:
    """Returns whether any months have stale summaries awaiting recompute."""
    db_file = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)
    with DatabaseSession(db_file) as session:
        months = session.dirty_months.get_all_dirty()
    return DirtyStatusResponse(
        dirty=len(months) > 0,
        months=[DirtyMonth(month=m, year=y) for m, y in months],
    )


@router.post("/recompute", response_model=RecomputeResponse)
async def recompute_summaries(background_tasks: BackgroundTasks) -> RecomputeResponse:
    """
    Triggers recompute of all dirty months. Runs in a background task so the
    response returns immediately; the client should poll /dirty or refetch summaries
    after a short delay.
    """
    db_file = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)
    with DatabaseSession(db_file) as session:
        dirty_months = session.dirty_months.get_all_dirty()

    if not dirty_months:
        return RecomputeResponse(recomputed=[])

    background_tasks.add_task(_recompute_dirty_months, dirty_months)
    return RecomputeResponse(
        recomputed=[DirtyMonth(month=m, year=y) for m, y in dirty_months]
    )


@router.get("/{month_str}")
async def get_monthly_summary(month_str: str) -> dict:
    """
    Returns the stored summary record for a given month. month_str format: YYYY-MM.
    """
    try:
        dt = datetime.strptime(month_str, "%Y-%m")
    except ValueError:
        raise HTTPException(status_code=422, detail="month_str must be in YYYY-MM format")

    db_file = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)
    with DatabaseSession(db_file) as session:
        rows = session.summaries.fetch_items_by_attribute(month=dt.month, year=dt.year)

    if not rows:
        raise HTTPException(status_code=404, detail=f"No summary found for {month_str}")

    row = rows[0]
    return {col.name: getattr(row, col.name) for col in row.__table__.columns}
