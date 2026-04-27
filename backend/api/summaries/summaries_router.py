#!python3
"""
backend.api.summaries.summaries_router

Endpoints for reading monthly summaries and managing the dirty-months recompute queue.
"""
# Standard library imports
from pleasant_loggers import get_logger
from datetime import datetime
from typing import Optional

# Third party imports
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

# Custom imports
from pleasant_database import DatabaseFile

# Local imports
from backend.database_modules.db_session import DatabaseSession
from backend.utils.analysis_utils import PrimaryCategories
from backend.utils.api_utils import RouterPrefixes
from backend.utils.file_utils import EDirectories

logger = get_logger(__name__)

router = APIRouter(prefix=RouterPrefixes.SUMMARIES.value, tags=["Summaries"])

_camel_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

_SNAKE_KEYS: list[str] = PrimaryCategories.as_snake_case_headers()
_DISPLAY_NAMES: list[str] = PrimaryCategories.as_list()
_SNAKE_TO_DISPLAY: dict[str, str] = dict(zip(_SNAKE_KEYS, _DISPLAY_NAMES))


# ─── Response models ──────────────────────────────────────────────────────────

class DirtyMonth(BaseModel):
    month: int
    year: int


class DirtyStatusResponse(BaseModel):
    dirty: bool
    months: list[DirtyMonth]


class RecomputeResponse(BaseModel):
    recomputed: list[DirtyMonth]


class CategorySpendResponse(BaseModel):
    model_config = _camel_config

    category_id: str
    category_name: str
    amount: float
    transaction_count: int
    avg_per_transaction: float
    monthly_limit: Optional[float] = None
    percent_of_limit: Optional[float] = None
    is_over_budget: bool


class MonthlySummaryResponse(BaseModel):
    model_config = _camel_config

    month: str
    total_income: float
    total_expenses: float
    net: float
    by_category: list[CategorySpendResponse]


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


def _build_monthly_summary(row, month_str: str, session: DatabaseSession) -> MonthlySummaryResponse:
    """Assemble a MonthlySummaryResponse from a summary ORM row."""
    budget_limits: dict[str, float] = {}
    if row.budget_id is not None:
        budget_row = session.budgets.fetch_item_by_id(row.budget_id)
        if budget_row:
            for snake_key, display_name in zip(_SNAKE_KEYS, _DISPLAY_NAMES):
                budget_limits[display_name] = getattr(budget_row, snake_key, 0.0) or 0.0

    by_category: list[CategorySpendResponse] = []
    for cat in PrimaryCategories:
        snake = cat.as_snake_case()
        amount = getattr(row, f"sum_{snake}", 0.0) or 0.0
        count = getattr(row, f"count_{snake}", 0) or 0
        mean = getattr(row, f"mean_{snake}", 0.0) or 0.0
        limit = budget_limits.get(cat.value)
        pct = (amount / limit * 100) if limit else None
        by_category.append(CategorySpendResponse(
            category_id=cat.value,
            category_name=cat.value,
            amount=amount,
            transaction_count=count,
            avg_per_transaction=mean,
            monthly_limit=limit,
            percent_of_limit=pct,
            is_over_budget=pct is not None and pct > 100,
        ))

    total_income = getattr(row, "sum_income", 0.0) or 0.0
    total_expenses = sum(
        getattr(row, f"sum_{cat.as_snake_case()}", 0.0) or 0.0
        for cat in PrimaryCategories
        if cat.value != "Income"
    )

    return MonthlySummaryResponse(
        month=month_str,
        total_income=total_income,
        total_expenses=total_expenses,
        net=total_income - total_expenses,
        by_category=by_category,
    )


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
    Returns MonthlySummary for a given month. month_str format: YYYY-MM.
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

        summary = _build_monthly_summary(rows[0], month_str, session)

    return {"data": summary.model_dump(by_alias=True)}
