#!python3
"""
backend.api.transactions.transactions_router

Contains FastAPI router for transaction-related endpoints, including fetching transactions
with optional filters/pagination and CSV import with async job tracking.

Functions:
"""
# Standard library imports
import json as json_lib
from pleasant_loggers import get_logger
import os
from datetime import datetime
from typing import Optional

# Third party imports
import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile
from uuid import uuid4

logger = get_logger(__name__)

# Custom imports
from pleasant_database import DatabaseFile, DatabaseManager

# Local imports
from backend.api.transactions.transactions_models import (
    BulkUpdateRequest,
    Transaction,
    TransactionFilters,
    TransactionUpdate,
    TransactionsPage,
    UploadJobResponse,
    ImportJobStatus,
)
from backend.database_modules.managers.transaction_manager import (
    TransactionsTableManager,
    UpdatesTableManager,
    UploadJobsManager,
)
from backend.database_modules.managers.rules_manager import TransactionRulesManager
from backend.database_modules.managers.dirty_months_manager import DirtyMonthsManager
from backend.database_modules.managers.summary_manager import SummariesTableManager
from backend.database_modules.models.transactions import TransactionsTable
from backend.utils.api_utils import RouterPrefixes
from backend.utils.file_utils import EDirectories


router = APIRouter(prefix=RouterPrefixes.TRANSACTIONS.value, tags=["Transactions"])

SORT_BY_COLUMN = {
    "date": TransactionsTable.authorized_date.name,
    "amount": TransactionsTable.amount.name,
}


def get_db():
    """
    Dependency function to get a database session for the transaction manager.
    Attached to live database file.
    """
    db_file = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)
    updates_mgr = UpdatesTableManager(db_file)
    db = TransactionsTableManager(db_file, updates_mgr)
    try:
        yield db
    finally:
        db.end_session()
        updates_mgr.end_session()


@router.get("", tags=["Transactions"], response_model=TransactionsPage)
async def get_transaction_pages(
    filters: TransactionFilters = Depends(),
    db: DatabaseManager = Depends(get_db)
) -> TransactionsPage:
    """
    API endpoint to fetch transactions with optional filters and pagination.

    Args:
        filters (TransactionFilters): Query parameters for filtering and pagination.
        db (DatabaseManager): Database session dependency.

    Returns:
        Paginated list of transactions matching the filters.
    """
    db_filters, tag_list = filters.to_db_filters()
    order_by_column = SORT_BY_COLUMN.get(filters.sort_by, TransactionsTable.authorized_date.name)

    result = db.query(
        columns=db.return_columns,
        filters=db_filters,
        order_by=order_by_column,
        ascending=filters.sort_ascending,
        limit=filters.page_size,
        offset=(filters.page - 1) * filters.page_size,
        search=filters.search,
        search_columns=db.search_columns,
    )

    transactions_df = result.data

    # Tags filtering uses OR logic — not supported by db filters, applied on the DataFrame
    if tag_list:
        masks = [transactions_df.tags.str.contains(tag, na=False) for tag in tag_list]
        combined_mask = masks[0]
        for mask in masks[1:]:
            combined_mask = combined_mask | mask
        transactions_df = transactions_df[combined_mask]

    transactions = transactions_df.to_dict(orient="records")

    return {
        "data": transactions,
        "total": result.total_count,
        "page": filters.page,
        "page_size": len(transactions),
        "has_next_page": result.has_next,
    }


# ─── Tags Endpoint (must be before /{transaction_id} to avoid route shadowing) ─

@router.get("/tags", response_model=list[str])
async def get_available_tags(db: DatabaseManager = Depends(get_db)) -> list[str]:
    """Returns a sorted list of all unique tags present in the transactions table."""
    result = db.query(columns=[TransactionsTable.tags.name])
    if result.data.empty:
        return []

    all_tags: set[str] = set()
    for tags_str in result.data[TransactionsTable.tags.name].dropna():
        for tag in tags_str.split(","):
            tag = tag.strip()
            if tag:
                all_tags.add(tag)

    return sorted(all_tags)


# ─── Transaction Update Endpoint ─────────────────────────────────────────────

# Maps TransactionUpdate field names (camelCase, matching the form exactly) to DB column names
_FIELD_TO_COLUMN = {
    # 'date' is handled separately (Pydantic field-name/type collision — see endpoint)
    "description":      "description",
    "account_name":     "account_name",
    "amount":           "amount",
    "primaryCategory":  "primary_category",
    "detailedCategory": "detailed_category",
    "isExcluded":       "exclude",
    "isRepayment":      "repayment",
    "notes":            "notes",
    "tags":             "tags",
}


@router.put("/{transaction_id}", response_model=Transaction)
async def update_transaction(
    transaction_id: int,
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> Transaction:
    """
    Updates an existing transaction. Only fields present in the request body are changed.
    Returns the updated transaction record.
    """
    raw = await request.body()
    raw_data: dict = json_lib.loads(raw)
    logger.info("PUT /transactions/%s body: %s", transaction_id, raw_data)

    # Extract 'date' before Pydantic validation: naming a Pydantic field 'date' shadows
    # the datetime.date type in its own annotation, causing type=none_required in Pydantic v2.
    date_str: str | None = raw_data.pop("date", None)

    # Normalise tags: DB stores as comma-joined string; frontend may send a string
    # (old response shape) or an array (correct shape).
    if "tags" in raw_data and isinstance(raw_data["tags"], str):
        raw_data["tags"] = [t.strip() for t in raw_data["tags"].split(",") if t.strip()]

    try:
        body = TransactionUpdate.model_validate(raw_data)
    except Exception as exc:
        logger.error("TransactionUpdate validation failed for id=%s: %s | body=%s", transaction_id, exc, raw_data)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    data = body.model_dump(exclude_unset=True)

    updates = {}

    # Handle date separately (extracted above to avoid Pydantic field/type name collision)
    if date_str:
        try:
            updates["authorized_date"] = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid date format '{date_str}'. Expected YYYY-MM-DD.")

    for form_field, value in data.items():
        db_col = _FIELD_TO_COLUMN.get(form_field)
        if db_col is None:
            continue
        if form_field == "tags":
            updates[db_col] = ",".join(value) if value else ""
        else:
            updates[db_col] = value

    if not updates:
        raise HTTPException(status_code=400, detail="No updatable fields provided")

    # Capture existing date before update so we can mark the old month dirty if date changes
    summary_dirty_fields = {"authorized_date", "primary_category", "detailed_category"}
    needs_dirty_mark = bool(summary_dirty_fields.intersection(updates))
    existing_date: datetime | None = None
    if needs_dirty_mark:
        existing = db.fetch_item_by_id(transaction_id)
        existing_date = getattr(existing, "authorized_date", None)

    db.update_item(transaction_id, **updates)

    if needs_dirty_mark and existing_date is not None:
        new_date: datetime = updates.get("authorized_date", existing_date)
        db_file = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)
        dirty_mgr = DirtyMonthsManager(db_file)
        dirty_mgr.mark_dirty(new_date.month, new_date.year)
        if "authorized_date" in updates and existing_date.month != new_date.month:
            dirty_mgr.mark_dirty(existing_date.month, existing_date.year)
        dirty_mgr.end_session()

    rules_db_file = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)
    rules_mgr = TransactionRulesManager(rules_db_file)
    rules_mgr.apply_rules_to_transaction(transaction_id, db)
    rules_mgr.end_session()

    result = db.query(
        columns=db.return_columns,
        filters={TransactionsTable.id.name: ("==", transaction_id)},
    )

    if result.data.empty:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")

    return result.data.to_dict(orient="records")[0]


# ─── CSV Import Endpoints ─────────────────────────────────────────────────────

def _process_csv_upload(job_id: str, tmp_path: str) -> None:
    """
    Background task: uploads a CSV file to the transactions table using the existing
    upload_csv() pipeline. Updates job status throughout and cleans up the temp file.

    Creates its own DB sessions — background tasks must not reuse the request session.
    """
    db_file = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)
    jobs_mgr = UploadJobsManager(db_file)
    updates_mgr = UpdatesTableManager(db_file)
    tx_mgr = TransactionsTableManager(db_file, updates_mgr)

    try:
        jobs_mgr.set_status(job_id, "processing")

        count_before = tx_mgr.count_items()
        updated_records = tx_mgr.upload_csv(tmp_path)
        count_after = tx_mgr.count_items()

        rows_imported = count_after - count_before
        rows_updated = len(updated_records)

        rules_mgr = TransactionRulesManager(db_file)
        rules_mgr.apply_rules_to_all(tx_mgr)
        rules_mgr.end_session()

        # Compute summaries for all months present in the DB after import
        summary_mgr = SummariesTableManager(db_file)
        all_tx_df = tx_mgr.to_dataframe()
        if not all_tx_df.empty and "authorized_date" in all_tx_df.columns:
            all_tx_df["authorized_date"] = pd.to_datetime(all_tx_df["authorized_date"])
            affected_months = (
                all_tx_df[["authorized_date"]]
                .assign(month=all_tx_df["authorized_date"].dt.month, year=all_tx_df["authorized_date"].dt.year)
                [["month", "year"]]
                .drop_duplicates()
                .itertuples(index=False)
            )
            for row in affected_months:
                summary_df = tx_mgr.generate_monthly_summary(row.month, row.year)
                if summary_df.empty:
                    continue
                summary_mgr.upsert_summary(row.month, row.year, summary_df)

        jobs_mgr.set_status(
            job_id, "complete",
            rows_imported=rows_imported,
            rows_updated=rows_updated,
        )

    except Exception as e:
        jobs_mgr.set_status(job_id, "failed", errors=str(e))

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        tx_mgr.end_session()
        updates_mgr.end_session()
        summary_mgr.end_session()
        jobs_mgr.end_session()


@router.post("/import", response_model=UploadJobResponse)
async def import_transactions_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> UploadJobResponse:
    """
    Accepts a CSV file upload, saves it to a temp path, creates a job record,
    and queues a background task to process it. Returns a job_id immediately.
    """
    tmp_path = f"/tmp/{uuid4()}_{file.filename}"
    contents = await file.read()
    try:
        contents.decode("utf-8")
    except UnicodeDecodeError:
        contents = contents.decode("latin-1").encode("utf-8")

    with open(tmp_path, "wb") as f:
        f.write(contents)

    db_file = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)
    jobs_mgr = UploadJobsManager(db_file)
    job_id = jobs_mgr.create_job(tmp_path)
    jobs_mgr.end_session()

    background_tasks.add_task(_process_csv_upload, job_id, tmp_path)

    return {"job_id": job_id, "status": "pending"}


@router.get("/import/{job_id}", response_model=ImportJobStatus)
async def get_import_job_status(job_id: str) -> ImportJobStatus:
    """Returns the current status and result counts for a CSV import job."""
    db_file = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)
    jobs_mgr = UploadJobsManager(db_file)
    job = jobs_mgr.get_job(job_id)
    jobs_mgr.end_session()

    if not job:
        raise HTTPException(status_code=404, detail=f"Import job '{job_id}' not found")

    return {
        "job_id": job.job_id,
        "status": job.status,
        "rows_imported": job.rows_imported,
        "rows_updated": job.rows_updated,
        "errors": job.errors,
    }


# ─── Similar Transactions Endpoint ───────────────────────────────────────────

@router.get("/similar", response_model=list[Transaction])
async def get_similar_transactions(
    description: str,
    account_name: str,
    exclude_id: Optional[int] = None,
    db: DatabaseManager = Depends(get_db),
) -> list[Transaction]:
    """
    Returns transactions sharing the same description AND account_name,
    optionally excluding a specific transaction id (the one being edited).
    """
    result = db.query(
        columns=db.return_columns,
        filters={
            TransactionsTable.description.name: ("==", description),
            TransactionsTable.account_name.name: ("==", account_name),
        },
    )
    rows = result.data.to_dict(orient="records")
    if exclude_id is not None:
        rows = [r for r in rows if r["id"] != exclude_id]
    return rows


# ─── Bulk Update Endpoint ─────────────────────────────────────────────────────

@router.post("/bulk-update")
async def bulk_update_transactions(
    body: BulkUpdateRequest,
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """
    Applies category and/or tag changes to the provided list of transaction IDs.
    Tags are merged with existing tags (not replaced).
    Optionally saves a rule for the match pattern.
    """
    if not body.transaction_ids:
        raise HTTPException(status_code=400, detail="transaction_ids must not be empty")

    updates_applied = 0
    for tx_id in body.transaction_ids:
        row_result = db.query(
            columns=db.return_columns,
            filters={TransactionsTable.id.name: ("==", tx_id)},
        )
        if row_result.data.empty:
            continue

        row = row_result.data.to_dict(orient="records")[0]
        col_updates: dict = {}

        if body.primary_category is not None:
            col_updates["primary_category"] = body.primary_category
        if body.detailed_category is not None:
            col_updates["detailed_category"] = body.detailed_category
        if body.exclude is not None:
            col_updates["exclude"] = body.exclude

        if body.tags:
            existing_tags: list[str] = [t for t in (row.get("tags") or "").split(",") if t]
            merged = list(dict.fromkeys(existing_tags + body.tags))  # preserve order, deduplicate
            col_updates["tags"] = ",".join(merged)

        if col_updates:
            db.update_item(tx_id, **col_updates)
            updates_applied += 1

    if body.save_as_rule and body.match_description and body.match_account_name:
        db_file = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)
        rules_mgr = TransactionRulesManager(db_file)
        rules_mgr.upsert_rule(
            match_description=body.match_description,
            match_account_name=body.match_account_name,
            primary_category=body.primary_category,
            detailed_category=body.detailed_category,
            tags=body.tags,
            exclude=body.exclude,
        )
        rules_mgr.end_session()

    return {"updated": updates_applied}


@router.post("/import/{job_id}/confirm", response_model=ImportJobStatus)
async def confirm_import_job(job_id: str) -> ImportJobStatus:
    """
    Acknowledges a completed import job. In the simplified pipeline (no staging table),
    data is already committed to the transactions table when processing finishes.
    This endpoint acts as the frontend's confirmation handshake.
    """
    db_file = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)
    jobs_mgr = UploadJobsManager(db_file)
    job = jobs_mgr.get_job(job_id)
    jobs_mgr.end_session()

    if not job:
        raise HTTPException(status_code=404, detail=f"Import job '{job_id}' not found")

    if job.status not in ("complete", "failed"):
        raise HTTPException(
            status_code=400,
            detail=f"Job is not yet finished (status: {job.status}). Poll GET /import/{{job_id}} first.",
        )

    return {
        "job_id": job.job_id,
        "status": job.status,
        "rows_imported": job.rows_imported,
        "rows_updated": job.rows_updated,
        "errors": job.errors,
    }
