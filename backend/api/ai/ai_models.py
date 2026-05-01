#!python3
"""
backend.api.ai.ai_models
Pydantic response models for AI-related endpoints.
"""
from typing import Optional

from pydantic import BaseModel

from backend.ai_modules.normalization_plan import AmountTransform, CategoryMapping


class PlanCSVResponse(BaseModel):
    column_map: dict[str, Optional[str]]
    category_map: dict[str, CategoryMapping]
    amount_transform: AmountTransform
    debit_column: Optional[str] = None
    credit_column: Optional[str] = None
    issues: list[str] = []
    unmapped_required_columns: list[str] = []
    used_cache: bool
    requires_manual_review: bool
