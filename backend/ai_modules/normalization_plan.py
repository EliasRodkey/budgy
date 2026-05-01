#!python3
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class AmountTransform(str, Enum):
    SIGNED = "signed"        # single column, negative = expense (already correct)
    INVERT = "invert"        # single column, positive = expense (needs negation)
    DEBIT_CREDIT = "debit_credit"  # separate debit + credit columns


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
    issues: list[str] = []
    # Required schema fields that could not be mapped (blocks import until resolved)
    unmapped_required_columns: list[str] = []
