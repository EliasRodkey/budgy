#!python3
"""
backend.api.categories.categories_router

Serves the category hierarchy (primary categories, detailed subcategories, and
exclude-from-analysis categories) derived from the authoritative Python enums in
analysis_utils.py. No database access — purely enum-derived data.

Also provides category detail and subcategory detail endpoints that aggregate
summary and transaction data for the Categories pages.
"""
from collections import defaultdict
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pleasant_database import DatabaseFile

from backend.api.categories.categories_models import (
    CategoryDetailResponse,
    SpendOverTimePoint,
    SubcategoryDetailResponse,
    SubcategorySpend,
    TransactionItem,
    VendorItem,
)
from backend.database_modules.db_session import DatabaseSession
from backend.database_modules.managers.common import convert_datetime_nums_to_range
from backend.database_modules.models.transactions import TransactionsTable
from backend.utils.analysis_utils import CATEGORY_MAPPING, DetailedCategories, PrimaryCategories
from backend.utils.api_utils import RouterPrefixes
from backend.utils.file_utils import EDirectories

router = APIRouter(prefix=RouterPrefixes.CATEGORIES.value, tags=["Categories"])

_VALID_PRIMARY: set[str] = {c.value for c in PrimaryCategories}
_VALID_DETAILED: set[str] = {c.value for c in DetailedCategories}


def get_db():
    db_file = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)
    session = DatabaseSession(db_file)
    try:
        yield session
    finally:
        session.close()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _orm_row_to_transaction_item(row: dict) -> TransactionItem:
    """Convert a transactions DataFrame row (dict) to a TransactionItem."""
    def _fmt_date(val) -> str:
        if val is None:
            return ""
        if hasattr(val, "strftime"):
            return val.strftime("%Y-%m-%d")
        return str(val)[:10]

    return TransactionItem(
        id=int(row.get("id", 0)),
        authorized_date=_fmt_date(row.get("authorized_date")),
        posted_date=_fmt_date(row.get("posted_date")),
        status=str(row.get("status", "")),
        account_name=str(row.get("account_name", "")),
        description=str(row.get("description", "")),
        primary_category=str(row.get("primary_category", "")),
        detailed_category=str(row.get("detailed_category", "")),
        amount=float(row.get("amount", 0.0)),
        repayment=bool(row.get("repayment", False)),
        exclude=bool(row.get("exclude", False)),
        notes=row.get("notes"),
        tags=[t.strip() for t in raw.split(",") if t.strip()] if (raw := row.get("tags")) else [],
    )


def _build_subcategory_spend(
    summary_rows: list,
    primary_cat: PrimaryCategories,
    budget_limit: Optional[float],
) -> list[SubcategorySpend]:
    """Aggregate all-time subcategory spend from summary rows for a primary category."""
    detailed_cats = CATEGORY_MAPPING.get(primary_cat, [])
    totals: dict[str, dict] = {}

    for dc in detailed_cats:
        snake = dc.as_snake_case()
        total_amount = sum(abs(getattr(r, f"sum_{snake}", 0.0) or 0.0) for r in summary_rows)
        total_count = sum(getattr(r, f"count_{snake}", 0) or 0 for r in summary_rows)
        if total_count > 0:
            totals[dc.value] = {"amount": total_amount, "count": total_count}

    result = []
    for name, data in sorted(totals.items(), key=lambda x: -x[1]["amount"]):
        amount = data["amount"]
        count = data["count"]
        result.append(SubcategorySpend(
            category_id=name,
            category_name=name,
            amount=amount,
            transaction_count=count,
            avg_per_transaction=amount / count if count > 0 else 0.0,
            monthly_limit=None,
            percent_of_limit=None,
            is_over_budget=False,
        ))
    return result


def _build_subcategory_spend_single_row(
    row,
    primary_cat: PrimaryCategories,
    budget_limit: Optional[float],
) -> list[SubcategorySpend]:
    """Build subcategory spend for a single summary row (current month)."""
    detailed_cats = CATEGORY_MAPPING.get(primary_cat, [])
    result = []

    for dc in detailed_cats:
        snake = dc.as_snake_case()
        amount = abs(getattr(row, f"sum_{snake}", 0.0) or 0.0)
        count = getattr(row, f"count_{snake}", 0) or 0
        if count == 0:
            continue
        result.append(SubcategorySpend(
            category_id=dc.value,
            category_name=dc.value,
            amount=amount,
            transaction_count=count,
            avg_per_transaction=amount / count,
            monthly_limit=None,
            percent_of_limit=None,
            is_over_budget=False,
        ))

    return sorted(result, key=lambda x: -x.amount)


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("")
def get_categories() -> dict:
    """
    Returns the full category hierarchy used by the frontend for dropdowns and filters.

    Response shape:
      primaryCategories  — ordered list of all 16 primary category display names
      categoryMapping    — maps each primary name to its list of detailed subcategory names
      excludeCategories  — detailed categories excluded from spending analysis
    """
    from backend.utils.analysis_utils import EXCLUDE_CATEGORIES
    return {
        "primaryCategories": [c.value for c in PrimaryCategories],
        "categoryMapping": {
            k.value: [v.value for v in vs] for k, vs in CATEGORY_MAPPING.items()
        },
        "excludeCategories": [c.value for c in EXCLUDE_CATEGORIES],
    }


@router.get("/{primary_category}/{detailed_category}")
async def get_subcategory_detail(
    primary_category: str,
    detailed_category: str,
    month: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    db: DatabaseSession = Depends(get_db),
) -> dict:
    """Returns aggregate and transaction data for a specific subcategory."""
    if primary_category not in _VALID_PRIMARY:
        raise HTTPException(status_code=404, detail=f"Unknown primary category: {primary_category!r}")
    if detailed_category not in _VALID_DETAILED:
        raise HTTPException(status_code=404, detail=f"Unknown detailed category: {detailed_category!r}")

    # Parse selected period
    now = datetime.now()
    if month is not None:
        try:
            dt = datetime.strptime(month, "%Y-%m")
            sel_month: Optional[int] = dt.month
            sel_year: int = dt.year
        except ValueError:
            raise HTTPException(status_code=422, detail="month must be in YYYY-MM format")
    elif year is not None:
        sel_month = None
        sel_year = year
    else:
        sel_month = None
        sel_year = now.year

    db_filters: dict = {
        "primary_category": ("==", primary_category),
        "detailed_category": ("==", detailed_category),
        "exclude": ("==", False),
    }
    if month is not None or year is not None:
        period_start, period_end = convert_datetime_nums_to_range(sel_month, sel_year)
        db_filters["authorized_date"] = ("between", (period_start, period_end))

    result = db.transactions.query(
        columns=db.transactions.return_columns,
        filters=db_filters,
        order_by=TransactionsTable.authorized_date.name,
        ascending=False,
    )
    rows = result.data.to_dict(orient="records")

    transaction_count = len(rows)
    total_amount = sum(abs(float(r.get("amount", 0.0))) for r in rows)
    avg_transaction_size = total_amount / transaction_count if transaction_count > 0 else 0.0

    vendor_totals: dict[str, dict] = defaultdict(lambda: {"amount": 0.0, "count": 0})
    for r in rows:
        name = str(r.get("description", ""))
        vendor_totals[name]["amount"] += abs(float(r.get("amount", 0.0)))
        vendor_totals[name]["count"] += 1

    top_vendors = sorted(
        [VendorItem(name=n, amount=v["amount"], count=v["count"]) for n, v in vendor_totals.items()],
        key=lambda x: -x.amount,
    )[:5]

    transactions = [_orm_row_to_transaction_item(r) for r in rows]

    # Spend over time — always all-time regardless of selected period
    dc_snake = DetailedCategories(detailed_category).as_snake_case()
    all_summary_rows = sorted(db.summaries.fetch_all_items(), key=lambda r: (r.year, r.month))
    spend_over_time = [
        SpendOverTimePoint(
            month=f"{r.year}-{r.month:02d}",
            amount=abs(getattr(r, f"sum_{dc_snake}", 0.0) or 0.0),
        )
        for r in all_summary_rows
    ]

    response = SubcategoryDetailResponse(
        primary_category=primary_category,
        detailed_category=detailed_category,
        transaction_count=transaction_count,
        avg_transaction_size=avg_transaction_size,
        spend_over_time=spend_over_time,
        top_vendors=top_vendors,
        transactions=transactions,
    )
    return {"data": response.model_dump(by_alias=True)}


@router.get("/{primary_category}")
async def get_category_detail(
    primary_category: str,
    month: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    db: DatabaseSession = Depends(get_db),
) -> dict:
    """Returns aggregate detail for a primary category including spend over time and selected-period data."""
    if primary_category not in _VALID_PRIMARY:
        raise HTTPException(status_code=404, detail=f"Unknown primary category: {primary_category!r}")

    try:
        primary_cat_enum = PrimaryCategories(primary_category)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Unknown primary category: {primary_category!r}")

    snake = primary_cat_enum.as_snake_case()

    # All summary rows sorted chronologically
    all_rows = sorted(
        db.summaries.fetch_all_items(),
        key=lambda r: (r.year, r.month),
    )

    spend_over_time = [
        SpendOverTimePoint(
            month=f"{r.year}-{r.month:02d}",
            amount=abs(getattr(r, f"sum_{snake}", 0.0) or 0.0),
        )
        for r in all_rows
    ]

    # All-time subcategory breakdown
    subcategories = _build_subcategory_spend(all_rows, primary_cat_enum, None)

    # Parse selected period (default: current month)
    now = datetime.now()
    if month is not None:
        try:
            dt = datetime.strptime(month, "%Y-%m")
            sel_month: Optional[int] = dt.month
            sel_year: int = dt.year
        except ValueError:
            raise HTTPException(status_code=422, detail="month must be in YYYY-MM format")
    elif year is not None:
        sel_month = None
        sel_year = year
    else:
        sel_month = now.month
        sel_year = now.year

    period_start, period_end = convert_datetime_nums_to_range(sel_month, sel_year)

    # Selected period rows
    period_rows = [
        r for r in all_rows
        if r.year == sel_year and (sel_month is None or r.month == sel_month)
    ]

    if sel_month is None:
        # Year view: aggregate across all months in the year
        current_month_total = sum(abs(getattr(r, f"sum_{snake}", 0.0) or 0.0) for r in period_rows)
        current_month_tx_count = sum(getattr(r, f"count_{snake}", 0) or 0 for r in period_rows)
        current_month_subcategories = _build_subcategory_spend(period_rows, primary_cat_enum, None)
    else:
        period_row = period_rows[0] if period_rows else None
        current_month_total = abs(getattr(period_row, f"sum_{snake}", 0.0) or 0.0) if period_row else 0.0
        current_month_tx_count = getattr(period_row, f"count_{snake}", 0) or 0 if period_row else 0
        current_month_subcategories = (
            _build_subcategory_spend_single_row(period_row, primary_cat_enum, None)
            if period_row else []
        )

    # Budget for selected period (annualize if year view)
    budget_source_row = max(period_rows, key=lambda r: (r.year, r.month)) if period_rows else None
    budget: Optional[float] = None
    if budget_source_row and budget_source_row.budget_id is not None:
        budget_row = db.budgets.fetch_item_by_id(budget_source_row.budget_id)
        if budget_row:
            monthly_budget = getattr(budget_row, snake, None)
            if monthly_budget:
                budget = monthly_budget * 12 if sel_month is None else monthly_budget

    # Year average: monthly totals for the selected year
    year_rows = [r for r in all_rows if r.year == sel_year]
    if year_rows:
        year_monthly_totals = [abs(getattr(r, f"sum_{snake}", 0.0) or 0.0) for r in year_rows]
        year_avg_spend = sum(year_monthly_totals) / len(year_monthly_totals)
    else:
        year_avg_spend = 0.0

    # Transactions for selected period
    tx_filters = {
        "primary_category": ("==", primary_category),
        "exclude": ("==", False),
        "authorized_date": ("between", (period_start, period_end)),
    }
    tx_result = db.transactions.query(
        columns=db.transactions.return_columns,
        filters=tx_filters,
        order_by=TransactionsTable.authorized_date.name,
        ascending=False,
    )
    current_month_transactions = [
        _orm_row_to_transaction_item(r)
        for r in tx_result.data.to_dict(orient="records")
    ]

    response = CategoryDetailResponse(
        primary_category=primary_category,
        spend_over_time=spend_over_time,
        subcategories=subcategories,
        current_month_subcategories=current_month_subcategories,
        budget=budget,
        current_month_total=current_month_total,
        current_month_tx_count=current_month_tx_count,
        year_avg_spend=year_avg_spend,
        current_month_transactions=current_month_transactions,
    )
    return {"data": response.model_dump(by_alias=True)}
