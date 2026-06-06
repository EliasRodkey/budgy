#!python3
"""
backend.utils.summary_utils
Shared helpers for assembling MonthlySummaryResponse from DB rows.
Used by both the summaries router and the AI summary endpoint.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from backend.database_modules.db_session import DatabaseSession
from backend.utils.analysis_utils import PrimaryCategories

_camel_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

_SNAKE_KEYS: list[str] = PrimaryCategories.as_snake_case_headers()
_DISPLAY_NAMES: list[str] = PrimaryCategories.as_list()
_SNAKE_TO_DISPLAY: dict[str, str] = dict(zip(_SNAKE_KEYS, _DISPLAY_NAMES))
_NON_SPENDING = {"Income", "Transfers", "Investments"}


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


def build_monthly_summary(row, month_str: str, session: DatabaseSession) -> MonthlySummaryResponse:
    """Assemble a MonthlySummaryResponse from a single summary ORM row."""
    budget_limits: dict[str, float] = {}
    if row.budget_id is not None:
        budget_row = session.budgets.fetch_item_by_id(row.budget_id)
        if budget_row:
            for snake_key, display_name in zip(_SNAKE_KEYS, _DISPLAY_NAMES):
                budget_limits[display_name] = getattr(budget_row, snake_key, 0.0) or 0.0

    by_category: list[CategorySpendResponse] = []
    for cat in PrimaryCategories:
        snake = cat.as_snake_case()
        amount = abs(getattr(row, f"sum_{snake}", 0.0) or 0.0)
        count = getattr(row, f"count_{snake}", 0) or 0
        mean = getattr(row, f"mean_{snake}", 0.0) or 0.0
        limit = budget_limits.get(cat.value) or None
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
        abs(getattr(row, f"sum_{cat.as_snake_case()}", 0.0) or 0.0)
        for cat in PrimaryCategories
        if cat.value not in _NON_SPENDING
    )

    return MonthlySummaryResponse(
        month=month_str,
        total_income=total_income,
        total_expenses=total_expenses,
        net=total_income - total_expenses,
        by_category=by_category,
    )


def build_yearly_summary(rows: list, year_str: str, session: DatabaseSession) -> MonthlySummaryResponse:
    """Aggregate multiple monthly summary rows into a yearly MonthlySummaryResponse."""
    most_recent_row = max(rows, key=lambda r: (r.year, r.month))

    budget_limits: dict[str, float] = {}
    if most_recent_row.budget_id is not None:
        budget_row = session.budgets.fetch_item_by_id(most_recent_row.budget_id)
        if budget_row:
            for snake_key, display_name in zip(_SNAKE_KEYS, _DISPLAY_NAMES):
                monthly_val = getattr(budget_row, snake_key, 0.0) or 0.0
                budget_limits[display_name] = monthly_val * 12

    by_category: list[CategorySpendResponse] = []
    for cat in PrimaryCategories:
        snake = cat.as_snake_case()
        amount = sum(abs(getattr(r, f"sum_{snake}", 0.0) or 0.0) for r in rows)
        count = sum(getattr(r, f"count_{snake}", 0) or 0 for r in rows)
        mean = amount / count if count > 0 else 0.0
        limit = budget_limits.get(cat.value) or None
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

    total_income = sum(getattr(r, "sum_income", 0.0) or 0.0 for r in rows)
    total_expenses = sum(
        sum(abs(getattr(r, f"sum_{cat.as_snake_case()}", 0.0) or 0.0) for r in rows)
        for cat in PrimaryCategories
        if cat.value not in _NON_SPENDING
    )

    return MonthlySummaryResponse(
        month=year_str,
        total_income=total_income,
        total_expenses=total_expenses,
        net=total_income - total_expenses,
        by_category=by_category,
    )


def build_period_summary(period: str, session: DatabaseSession) -> Optional[MonthlySummaryResponse]:
    """
    Parse a period string (YYYY-MM or YYYY) and return a MonthlySummaryResponse,
    or None if no data exists. Raises ValueError on an unrecognised format.
    """
    # Try YYYY-MM (monthly)
    try:
        dt = datetime.strptime(period, "%Y-%m")
        rows = session.summaries.fetch_items_by_attribute(month=dt.month, year=dt.year)
        if not rows:
            return None
        return build_monthly_summary(rows[0], period, session)
    except ValueError:
        pass

    # Try YYYY (yearly)
    try:
        year = int(period)
        if len(period) != 4:
            raise ValueError
        rows = [r for r in session.summaries.fetch_all_items() if r.year == year]
        if not rows:
            return None
        return build_yearly_summary(rows, period, session)
    except ValueError:
        pass

    raise ValueError(f"period must be YYYY-MM or YYYY, got: {period!r}")
