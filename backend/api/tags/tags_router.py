#!python3
"""
backend.api.tags.tags_router

Serves tag overview and tag detail data for the Tags pages. Tags are stored as a
comma-separated string column on the transactions table — there is no precomputed
summary table for tags, so all aggregation here is computed on-the-fly from the
transactions table via pandas.
"""
from collections import defaultdict

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pleasant_database import DatabaseFile

from backend.api.tags.tags_models import (
    SpendOverTimePoint,
    TagCategorySpend,
    TagDetailResponse,
    TagSummary,
    TransactionItem,
)
from backend.database_modules.db_session import DatabaseSession
from backend.database_modules.models.transactions import TransactionsTable
from backend.utils.api_utils import RouterPrefixes
from backend.utils.file_utils import EDirectories

router = APIRouter(prefix=RouterPrefixes.TAGS.value, tags=["Tags"])


def get_db():
    db_file = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)
    session = DatabaseSession(db_file)
    try:
        yield session
    finally:
        session.close()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _parse_tags(raw) -> list[str]:
    """Parse a comma-separated tags string into a list of trimmed, non-empty tags."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return []
    return [t.strip() for t in str(raw).split(",") if t.strip()]


def _orm_row_to_transaction_item(row: dict) -> TransactionItem:
    """Convert a transactions DataFrame row (dict) to a TransactionItem."""
    def _fmt_date(val) -> str:
        if val is None:
            return ""
        if hasattr(val, "strftime"):
            return val.strftime("%Y-%m-%d")
        return str(val)[:10]

    return TransactionItem(
        id=int(row.get(TransactionsTable.id.name, 0)),
        authorized_date=_fmt_date(row.get(TransactionsTable.authorized_date.name)),
        posted_date=_fmt_date(row.get(TransactionsTable.posted_date.name)),
        status=str(row.get(TransactionsTable.status.name, "")),
        account_name=str(row.get(TransactionsTable.account_name.name, "")),
        description=str(row.get(TransactionsTable.description.name, "")),
        primary_category=str(row.get(TransactionsTable.primary_category.name, "")),
        detailed_category=str(row.get(TransactionsTable.detailed_category.name, "")),
        amount=float(row.get(TransactionsTable.amount.name, 0.0)),
        repayment=bool(row.get(TransactionsTable.repayment.name, False)),
        exclude=bool(row.get(TransactionsTable.exclude.name, False)),
        notes=row.get(TransactionsTable.notes.name),
        tags=_parse_tags(row.get(TransactionsTable.tags.name)),
    )


def _build_category_breakdown(rows: list[dict]) -> list[TagCategorySpend]:
    """Aggregate spend per primary category across the given transaction rows."""
    totals: dict[str, dict] = defaultdict(lambda: {"amount": 0.0, "count": 0})
    for r in rows:
        name = str(r.get(TransactionsTable.primary_category.name, ""))
        totals[name]["amount"] += abs(float(r.get(TransactionsTable.amount.name, 0.0)))
        totals[name]["count"] += 1

    result = [
        TagCategorySpend(
            category_id=name,
            category_name=name,
            amount=data["amount"],
            transaction_count=data["count"],
            avg_per_transaction=data["amount"] / data["count"],
        )
        for name, data in totals.items()
    ]
    return sorted(result, key=lambda x: -x.amount)


def _build_spend_over_time(tag_df: pd.DataFrame) -> list[SpendOverTimePoint]:
    """Monthly spend totals for the tag, zero-filled across the full date range."""
    months = pd.to_datetime(tag_df[TransactionsTable.authorized_date.name]).dt.to_period("M")
    monthly_totals = tag_df[TransactionsTable.amount.name].abs().groupby(months).sum()

    full_range = pd.period_range(start=months.min(), end=months.max(), freq="M")
    return [
        SpendOverTimePoint(month=str(period), amount=float(monthly_totals.get(period, 0.0)))
        for period in full_range
    ]


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("")
async def get_tags_overview(db: DatabaseSession = Depends(get_db)) -> dict:
    """Returns total spend and transaction count for every tag, sorted by spend descending."""
    result = db.transactions.query(
        columns=db.transactions.return_columns,
        filters={TransactionsTable.exclude.name: ("==", False)},
    )
    df = result.data
    if df.empty:
        return {"data": []}

    tag_lists = df[TransactionsTable.tags.name].apply(_parse_tags)
    exploded = df.assign(_tag=tag_lists).explode("_tag")
    exploded = exploded[exploded["_tag"].notna() & (exploded["_tag"] != "")]

    if exploded.empty:
        return {"data": []}

    amounts = exploded[TransactionsTable.amount.name].abs()
    totals = amounts.groupby(exploded["_tag"]).sum()
    counts = exploded.groupby("_tag").size()

    summaries = [
        TagSummary(
            tag_name=tag,
            total_spend=float(totals[tag]),
            transaction_count=int(counts[tag]),
        )
        for tag in totals.index
    ]
    summaries.sort(key=lambda t: -t.total_spend)
    return {"data": [s.model_dump(by_alias=True) for s in summaries]}


@router.get("/{tag_name}")
async def get_tag_detail(tag_name: str, db: DatabaseSession = Depends(get_db)) -> dict:
    """Returns aggregate spend, category breakdown, and transactions for a single tag."""
    result = db.transactions.query(
        columns=db.transactions.return_columns,
        filters={TransactionsTable.exclude.name: ("==", False)},
        order_by=TransactionsTable.authorized_date.name,
        ascending=False,
    )
    df = result.data
    if not df.empty:
        tag_lists = df[TransactionsTable.tags.name].apply(_parse_tags)
        tag_df = df[tag_lists.apply(lambda tags: tag_name in tags)]
    else:
        tag_df = df

    if tag_df.empty:
        raise HTTPException(status_code=404, detail=f"Unknown tag: {tag_name!r}")

    rows = tag_df.to_dict(orient="records")
    total_spend = sum(abs(float(r.get(TransactionsTable.amount.name, 0.0))) for r in rows)

    response = TagDetailResponse(
        tag_name=tag_name,
        total_spend=total_spend,
        transaction_count=len(rows),
        spend_over_time=_build_spend_over_time(tag_df),
        category_breakdown=_build_category_breakdown(rows),
        transactions=[_orm_row_to_transaction_item(r) for r in rows],
    )
    return {"data": response.model_dump(by_alias=True)}
