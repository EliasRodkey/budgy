#!python3
"""
backend.api.budgets.budgets_router
Full CRUD for /budgets and /budgets/assignments.
"""
from datetime import datetime

from pleasant_loggers import get_logger
from fastapi import APIRouter, Depends, HTTPException, Response

from pleasant_database import DatabaseFile

from backend.database_modules.db_session import DatabaseSession
from backend.utils.api_utils import RouterPrefixes
from backend.utils.file_utils import EDirectories
from backend.api.budgets.budgets_models import (
    BudgetAssignmentCreate,
    BudgetAssignmentResponse,
    BudgetCreate,
    BudgetResponse,
    BudgetUpdate,
    budget_create_to_db_kwargs,
    db_row_to_budget_response,
)

logger = get_logger(__name__)

router = APIRouter(prefix=RouterPrefixes.BUDGETS.value, tags=["Budgets"])


def get_db():
    db_file = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)
    session = DatabaseSession(db_file)
    try:
        yield session
    finally:
        session.close()


# ─── Budget Assignments (registered BEFORE /{budget_id} to avoid path shadowing) ──

@router.get("/assignments", response_model=list[BudgetAssignmentResponse])
async def get_budget_assignments(
    db: DatabaseSession = Depends(get_db),
) -> list[BudgetAssignmentResponse]:
    rows = db.budget_assignments.get_all()
    return [
        BudgetAssignmentResponse(
            id=r.id,
            budget_id=r.budget_id,
            effective_from=r.effective_from,
            note=r.note,
        )
        for r in rows
    ]


@router.post("/assignments", response_model=BudgetAssignmentResponse, status_code=201)
async def create_budget_assignment(
    payload: BudgetAssignmentCreate,
    db: DatabaseSession = Depends(get_db),
) -> BudgetAssignmentResponse:
    try:
        db.budgets.fetch_item_by_id(payload.budget_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Budget {payload.budget_id} not found")

    db.budget_assignments.add_item(
        budget_id=payload.budget_id,
        effective_from=payload.effective_from,
        note=payload.note,
    )
    all_rows = db.budget_assignments.get_all()
    row = max(all_rows, key=lambda r: r.id)
    return BudgetAssignmentResponse(
        id=row.id,
        budget_id=row.budget_id,
        effective_from=row.effective_from,
        note=row.note,
    )


@router.delete("/assignments/{assignment_id}", status_code=204)
async def delete_budget_assignment(
    assignment_id: int,
    db: DatabaseSession = Depends(get_db),
) -> Response:
    try:
        db.budget_assignments.fetch_item_by_id(assignment_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Assignment {assignment_id} not found")
    db.budget_assignments.delete_item(assignment_id)
    return Response(status_code=204)


# ─── Budget CRUD ──────────────────────────────────────────────────────────────

@router.get("", response_model=list[BudgetResponse])
async def get_budgets(db: DatabaseSession = Depends(get_db)) -> list[BudgetResponse]:
    rows = db.budgets.get_all()
    return [db_row_to_budget_response(r) for r in rows]


@router.post("", response_model=BudgetResponse, status_code=201)
async def create_budget(
    payload: BudgetCreate,
    db: DatabaseSession = Depends(get_db),
) -> BudgetResponse:
    kwargs = budget_create_to_db_kwargs(payload)
    kwargs["date_created"] = datetime.now()
    db.budgets.add_item(**kwargs)
    all_rows = db.budgets.get_all()
    if not all_rows:
        raise HTTPException(status_code=500, detail="Budget creation failed")
    row = max(all_rows, key=lambda r: r.id)
    return db_row_to_budget_response(row)


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: int,
    payload: BudgetUpdate,
    db: DatabaseSession = Depends(get_db),
) -> BudgetResponse:
    try:
        existing = db.budgets.fetch_item_by_id(budget_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Budget {budget_id} not found")

    from backend.api.budgets.budgets_models import _DISPLAY_TO_SNAKE, _EXPENSE_SNAKE_KEYS

    updates: dict = {}
    if payload.monthly_income_estimate is not None:
        updates["income"] = payload.monthly_income_estimate
    if payload.category_limits is not None:
        for display_name, value in payload.category_limits.items():
            snake_key = _DISPLAY_TO_SNAKE.get(display_name)
            if snake_key:
                updates[snake_key] = value
    if payload.note is not None:
        updates["note"] = payload.note

    income = updates.get("income", existing.income or 0)
    total_expenses = sum(updates.get(k, getattr(existing, k, 0) or 0) for k in _EXPENSE_SNAKE_KEYS)
    updates["net_gain_or_loss"] = income - total_expenses

    db.budgets.update_item(budget_id, **updates)
    row = db.budgets.fetch_item_by_id(budget_id)
    return db_row_to_budget_response(row)


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(
    budget_id: int,
    db: DatabaseSession = Depends(get_db),
) -> Response:
    try:
        db.budgets.fetch_item_by_id(budget_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Budget {budget_id} not found")
    db.budgets.delete_by_id(budget_id)
    return Response(status_code=204)
