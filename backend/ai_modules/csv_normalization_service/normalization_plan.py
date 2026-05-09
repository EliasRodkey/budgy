#!python3
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class AmountTransform(str, Enum):
    EXPENSE_NEGATIVE = "expense_negative"  # single column, expenses are negative (standard, no change needed)
    EXPENSE_POSITIVE = "expense_positive"  # single column, expenses are positive (must negate on import)
    DEBIT_CREDIT = "debit_credit"          # separate debit + credit columns


class CategoryMapping(BaseModel):
    primary: str
    detailed: str


class NormalizationPlan(BaseModel):
    # Maps raw CSV header -> Budgy schema field name (None = unmappable)
    column_map: dict[str, Optional[str]]
    # Maps raw category string -> {primary, detailed}
    category_map: dict[str, CategoryMapping]
    amount_transform: AmountTransform
    debit_column: Optional[str] = None   # set when amount_transform == debit_credit
    credit_column: Optional[str] = None  # set when amount_transform == debit_credit
    issues: list[str] = []               # file-level structural errors and unresolvable ambiguities only
    # Required schema fields that could not be mapped (blocks import until resolved)
    unmapped_required_columns: list[str] = []
    # Per-section AI reasoning, shown inline in the review UI
    column_map_reasoning: Optional[str] = None
    category_map_reasoning: Optional[str] = None
    amount_transform_reasoning: Optional[str] = None
