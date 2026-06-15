#!python3
"""
backend.api.tags.tags_models
Pydantic response models for the tags overview and tag detail endpoints.
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

_camel_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class TagSummary(BaseModel):
    model_config = _camel_config

    tag_name: str
    total_spend: float
    transaction_count: int


class SpendOverTimePoint(BaseModel):
    model_config = _camel_config

    month: str
    amount: float


class TagCategorySpend(BaseModel):
    model_config = _camel_config

    category_id: str
    category_name: str
    amount: float
    transaction_count: int
    avg_per_transaction: float
    monthly_limit: Optional[float] = None
    percent_of_limit: Optional[float] = None
    is_over_budget: bool = False


class TransactionItem(BaseModel):
    model_config = _camel_config

    id: int
    authorized_date: str
    posted_date: str
    status: str
    account_name: str
    description: str
    primary_category: str
    detailed_category: str
    amount: float
    repayment: bool
    exclude: bool
    notes: Optional[str] = None
    tags: list[str] = []


class TagDetailResponse(BaseModel):
    model_config = _camel_config

    tag_name: str
    total_spend: float
    transaction_count: int
    spend_over_time: list[SpendOverTimePoint]
    category_breakdown: list[TagCategorySpend]
    transactions: list[TransactionItem]
