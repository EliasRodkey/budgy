#!python3
"""
backend.api.rules.rules_router
CRUD endpoints for transaction rules (transaction_rules table), plus a
matched-transactions preview endpoint.
"""
from pleasant_loggers import get_logger
from fastapi import APIRouter, Depends, HTTPException, Response

from pleasant_database import DatabaseFile, DatabaseIntegrityError

from backend.database_modules.db_session import DatabaseSession
from backend.database_modules.models.transactions import TransactionsTable
from backend.utils.api_utils import RouterPrefixes
from backend.utils.file_utils import EDirectories
from backend.api.transactions.transactions_models import Transaction
from backend.api.rules.rules_models import (
    RuleCreate,
    RuleResponse,
    RuleUpdate,
    db_row_to_rule_response,
)

logger = get_logger(__name__)

router = APIRouter(prefix=RouterPrefixes.RULES.value, tags=["Rules"])

MATCHES_PREVIEW_LIMIT = 20


def get_db():
    db_file = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)
    session = DatabaseSession(db_file)
    try:
        yield session
    finally:
        session.close()


def _apply_rules_and_mark_dirty(db: DatabaseSession) -> None:
    """Re-apply all rules to all matching transactions and mark affected months dirty."""
    affected_months = db.rules.apply_rules_to_all(db.transactions)
    for month, year in affected_months:
        db.dirty_months.mark_dirty(month, year)


def _matching_transactions(db: DatabaseSession, match_description: str, match_account_name: str) -> list:
    result = db.transactions.query(
        columns=db.transactions.return_columns,
        filters={
            TransactionsTable.description.name: ("==", match_description),
            TransactionsTable.account_name.name: ("==", match_account_name),
        },
    )
    return result.data.to_dict(orient="records")


# ─── Rule CRUD ────────────────────────────────────────────────────────────────

@router.get("")
async def list_rules(db: DatabaseSession = Depends(get_db)) -> dict:
    rules = db.rules.list_rules()
    return {"data": [db_row_to_rule_response(r).model_dump(by_alias=True) for r in rules]}


@router.post("", response_model=RuleResponse, status_code=201)
async def create_rule(
    payload: RuleCreate,
    db: DatabaseSession = Depends(get_db),
) -> RuleResponse:
    existing = db.rules.get_rule(payload.match_description, payload.match_account_name)
    if existing:
        raise HTTPException(
            status_code=409,
            detail="A rule already exists for this description and account name.",
        )

    rule = db.rules.upsert_rule(
        match_description=payload.match_description,
        match_account_name=payload.match_account_name,
        primary_category=payload.primary_category,
        detailed_category=payload.detailed_category,
        exclude=payload.exclude,
    )
    _apply_rules_and_mark_dirty(db)
    return db_row_to_rule_response(rule)


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: int,
    payload: RuleUpdate,
    db: DatabaseSession = Depends(get_db),
) -> RuleResponse:
    try:
        db.rules.fetch_item_by_id(rule_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

    try:
        rule = db.rules.update_rule(
            rule_id,
            match_description=payload.match_description,
            match_account_name=payload.match_account_name,
            primary_category=payload.primary_category,
            detailed_category=payload.detailed_category,
            exclude=payload.exclude,
        )
    except DatabaseIntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="A rule already exists for this description and account name.",
        ) from exc

    _apply_rules_and_mark_dirty(db)
    return db_row_to_rule_response(rule)


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: int,
    db: DatabaseSession = Depends(get_db),
) -> Response:
    try:
        db.rules.fetch_item_by_id(rule_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

    db.rules.delete_rule(rule_id)
    return Response(status_code=204)


# ─── Matched transactions preview ────────────────────────────────────────────

@router.get("/{rule_id}/matches")
async def get_rule_matches(
    rule_id: int,
    db: DatabaseSession = Depends(get_db),
) -> dict:
    try:
        rule = db.rules.fetch_item_by_id(rule_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

    rows = _matching_transactions(db, rule.match_description, rule.match_account_name)
    transactions = [Transaction.model_validate(r) for r in rows[:MATCHES_PREVIEW_LIMIT]]
    return {
        "matchCount": len(rows),
        "transactions": [t.model_dump(by_alias=True) for t in transactions],
    }
