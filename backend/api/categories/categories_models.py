#!python3
"""
backend.api.categories.categories_models
Pydantic response models for category detail endpoints.
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

_camel_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class SubcategorySpend(BaseModel):
    model_config = _camel_config

    category_id: str
    category_name: str
    amount: float
    transaction_count: int
    avg_per_transaction: float
    monthly_limit: Optional[float] = None
    percent_of_limit: Optional[float] = None
    is_over_budget: bool


class SpendOverTimePoint(BaseModel):
    model_config = _camel_config

    month: str
    amount: float


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


class CategoryDetailResponse(BaseModel):
    model_config = _camel_config

    primary_category: str
    spend_over_time: list[SpendOverTimePoint]
    subcategories: list[SubcategorySpend]
    current_month_subcategories: list[SubcategorySpend]
    budget: Optional[float] = None
    current_month_total: float
    current_month_tx_count: int
    year_avg_spend: float
    current_month_transactions: list[TransactionItem]


class VendorItem(BaseModel):
    model_config = _camel_config

    name: str
    amount: float
    count: int


class SubcategoryDetailResponse(BaseModel):
    model_config = _camel_config

    primary_category: str
    detailed_category: str
    transaction_count: int
    avg_transaction_size: float
    spend_over_time: list[SpendOverTimePoint] = []
    top_vendors: list[VendorItem]
    transactions: list[TransactionItem]
