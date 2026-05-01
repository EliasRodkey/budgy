#!python3
"""
backend.api.budgets.budgets_models
Pydantic models and serialization helpers for the budgets API.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.alias_generators import to_camel

from backend.utils.analysis_utils import PrimaryCategories

# Build once: snake_case_key → display_name (e.g. "food_and_drink" → "Food & drink")
# and the inverse for deserialization.
_SNAKE_KEYS: list[str] = PrimaryCategories.as_snake_case_headers()
_DISPLAY_NAMES: list[str] = PrimaryCategories.as_list()
_SNAKE_TO_DISPLAY: dict[str, str] = dict(zip(_SNAKE_KEYS, _DISPLAY_NAMES))
_DISPLAY_TO_SNAKE: dict[str, str] = dict(zip(_DISPLAY_NAMES, _SNAKE_KEYS))

# Categories that count toward spending and net_gain_or_loss
_SPENDING_SNAKE_KEYS: list[str] = [
    k for k in _SNAKE_KEYS
    if k not in ("income", "transfers", "debt_payments", "investments", "bank_fees")
]
# Categories shown/editable in the budget but NOT counted in net_gain_or_loss
_TRACKING_SNAKE_KEYS: list[str] = ["investments"]
# All keys included in the categoryLimits API response (spending + tracking)
_RESPONSE_SNAKE_KEYS: list[str] = _SPENDING_SNAKE_KEYS + _TRACKING_SNAKE_KEYS
# Alias kept for any internal callers that still reference _EXPENSE_SNAKE_KEYS
_EXPENSE_SNAKE_KEYS: list[str] = _SPENDING_SNAKE_KEYS
# Valid display names accepted in create/update payloads
_VALID_DISPLAY_NAMES: set[str] = {_SNAKE_TO_DISPLAY[k] for k in _RESPONSE_SNAKE_KEYS}


_camel_config = ConfigDict(
    alias_generator=to_camel,
    populate_by_name=True,
)


# ─── Response models ──────────────────────────────────────────────────────────

class BudgetResponse(BaseModel):
    model_config = _camel_config

    id: int
    date_created: datetime
    monthly_income_estimate: float
    net_gain_or_loss: float
    category_limits: dict[str, float]
    note: Optional[str] = None


class BudgetAssignmentResponse(BaseModel):
    model_config = _camel_config

    id: int
    budget_id: int
    effective_from: str
    note: Optional[str] = None


# ─── Request models ───────────────────────────────────────────────────────────

class BudgetCreate(BaseModel):
    model_config = _camel_config

    monthly_income_estimate: float
    category_limits: dict[str, float]
    note: Optional[str] = None

    @field_validator("category_limits")
    @classmethod
    def validate_category_keys(cls, v: dict[str, float]) -> dict[str, float]:
        invalid = set(v.keys()) - _VALID_DISPLAY_NAMES
        if invalid:
            raise ValueError(f"Unknown category limit keys: {invalid}")
        return v


class BudgetUpdate(BaseModel):
    model_config = _camel_config

    monthly_income_estimate: Optional[float] = None
    category_limits: Optional[dict[str, float]] = None
    note: Optional[str] = None

    @field_validator("category_limits")
    @classmethod
    def validate_category_keys(cls, v: Optional[dict[str, float]]) -> Optional[dict[str, float]]:
        if v is None:
            return v
        invalid = set(v.keys()) - _VALID_DISPLAY_NAMES
        if invalid:
            raise ValueError(f"Unknown category limit keys: {invalid}")
        return v


class BudgetAssignmentCreate(BaseModel):
    model_config = _camel_config

    budget_id: int
    effective_from: str
    note: Optional[str] = None


# ─── Serialization helpers ────────────────────────────────────────────────────

def db_row_to_budget_response(row) -> BudgetResponse:
    """Convert a BudgetsTable ORM row to a BudgetResponse."""
    category_limits = {
        _SNAKE_TO_DISPLAY[k]: getattr(row, k, 0) or 0
        for k in _RESPONSE_SNAKE_KEYS
    }
    return BudgetResponse(
        id=row.id,
        date_created=row.date_created,
        monthly_income_estimate=row.income or 0,
        net_gain_or_loss=row.net_gain_or_loss or 0,
        category_limits=category_limits,
        note=row.note,
    )


def budget_create_to_db_kwargs(payload: BudgetCreate) -> dict:
    """Convert a BudgetCreate payload to the flat column kwargs expected by BudgetsTable."""
    kwargs: dict = {"income": payload.monthly_income_estimate}
    if payload.note is not None:
        kwargs["note"] = payload.note
    for display_name, snake_key in _DISPLAY_TO_SNAKE.items():
        if display_name == "Income":
            continue
        kwargs[snake_key] = (payload.category_limits or {}).get(display_name, 0.0)
    # net_gain_or_loss = income - sum(spending limits; investments excluded)
    total_expenses = sum(kwargs[k] for k in _SPENDING_SNAKE_KEYS)
    kwargs["net_gain_or_loss"] = payload.monthly_income_estimate - total_expenses
    return kwargs
