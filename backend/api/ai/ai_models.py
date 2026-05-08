#!python3
"""
backend.api.ai.ai_models
Pydantic response models for AI-related endpoints.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from backend.ai_modules.csv_normalization_service.normalization_plan import AmountTransform, CategoryMapping


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


class AISummaryData(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    generated_at: datetime
    recap: str
    anomalies: list[str]
    suggestions: list[str]


class AISummaryResponse(BaseModel):
    data: AISummaryData
