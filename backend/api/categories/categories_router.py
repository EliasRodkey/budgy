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

from fastapi import APIRouter, Depends, HTTPException
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
        tags=row.get("tags"),
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
        total_amount = sum(getattr(r, f"sum_{snake}", 0.0) or 0.0 for r in summary_rows)
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
        amount = getattr(row, f"sum_{snake}", 0.0) or 0.0
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
    db: DatabaseSession = Depends(get_db),
) -> dict:
    """Returns aggregate and transaction data for a specific subcategory."""
    if primary_category not in _VALID_PRIMARY:
        raise HTTPException(status_code=404, detail=f"Unknown primary category: {primary_category!r}")
    if detailed_category not in _VALID_DETAILED:
        raise HTTPException(status_code=404, detail=f"Unknown detailed category: {detailed_category!r}")

    db_filters = {
        "primary_category": ("==", primary_category),
        "detailed_category": ("==", detailed_category),
        "exclude": ("==", False),
    }
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
        name = str(r.get("account_name", ""))
        vendor_totals[name]["amount"] += abs(float(r.get("amount", 0.0)))
        vendor_totals[name]["count"] += 1

    top_vendors = sorted(
        [VendorItem(name=n, amount=v["amount"], count=v["count"]) for n, v in vendor_totals.items()],
        key=lambda x: -x.amount,
    )[:5]

    transactions = [_orm_row_to_transaction_item(r) for r in rows]

    response = SubcategoryDetailResponse(
        primary_category=primary_category,
        detailed_category=detailed_category,
        transaction_count=transaction_count,
        avg_transaction_size=avg_transaction_size,
        top_vendors=top_vendors,
        transactions=transactions,
    )
    return {"data": response.model_dump(by_alias=True)}


@router.get("/{primary_category}")
async def get_category_detail(
    primary_category: str,
    db: DatabaseSession = Depends(get_db),
) -> dict:
    """Returns aggregate detail for a primary category including spend over time and current-month data."""
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
            amount=getattr(r, f"sum_{snake}", 0.0) or 0.0,
        )
        for r in all_rows
    ]

    # All-time subcategory breakdown
    subcategories = _build_subcategory_spend(all_rows, primary_cat_enum, None)

    # Current month
    now = datetime.now()
    current_year, current_month = now.year, now.month
    current_rows = [r for r in all_rows if r.year == current_year and r.month == current_month]
    current_row = current_rows[0] if current_rows else None

    current_month_total = getattr(current_row, f"sum_{snake}", 0.0) or 0.0 if current_row else 0.0
    current_month_tx_count = getattr(current_row, f"count_{snake}", 0) or 0 if current_row else 0
    current_month_subcategories = (
        _build_subcategory_spend_single_row(current_row, primary_cat_enum, None)
        if current_row else []
    )

    # Budget for current month
    budget: Optional[float] = None
    if current_row and current_row.budget_id is not None:
        budget_row = db.budgets.fetch_item_by_id(current_row.budget_id)
        if budget_row:
            budget = getattr(budget_row, snake, None)

    # Year average: monthly totals for rows in the current year
    year_rows = [r for r in all_rows if r.year == current_year]
    if year_rows:
        year_monthly_totals = [getattr(r, f"sum_{snake}", 0.0) or 0.0 for r in year_rows]
        year_avg_spend = sum(year_monthly_totals) / len(year_monthly_totals)
    else:
        year_avg_spend = 0.0

    # Current month transactions
    month_start = datetime(current_year, current_month, 1)
    if current_month == 12:
        month_end = datetime(current_year + 1, 1, 1).replace(
            hour=23, minute=59, second=59
        )
    else:
        month_end = datetime(current_year, current_month + 1, 1).replace(
            hour=23, minute=59, second=59
        )

    tx_filters = {
        "primary_category": ("==", primary_category),
        "exclude": ("==", False),
        "authorized_date": ("between", (month_start, month_end)),
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
