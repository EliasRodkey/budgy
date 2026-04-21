#!python3
"""
backend.api.transactions.transactinos_models
Contains Pydantic models for transaction-related API endpoints, 
including request and response schemas for fetching transactions with optional month/year filters and pagination.
"""
# Standard library imports
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Optional

# Third party imports
from fastapi import Query


incoming_config = ConfigDict(
    from_attributes=True, # Enforce pydantic model validation
    populate_by_name=True, # Accept both camelCase and snake_case for incoming data.
    alias_generator=to_camel # Convert to camelCase for front end consumption.
)

outgoing_config = ConfigDict(
    populate_by_name=True, # Accept both camelCase and snake_case for incoming data.
    alias_generator=to_camel # Convert to camelCase for front end consumption.
)



class Transaction(BaseModel):
    id: int
    authorized_date: date
    posted_date: date
    status: str
    account_name: str
    description: str
    primary_category: str
    detailed_category: str
    amount: float # dollars (negative = expense)
    repayment: bool
    exclude: bool
    notes: Optional[str] = None # max 300 chars, edit modal only
    tags: Optional[str] = None # max 10 tags, each max 30 chars, no spaces

    model_config = outgoing_config



class TransactionFilters(BaseModel):
    search: Optional[str] = Query(None)
    primary_category: Optional[str] = Query(None)
    detailed_category: Optional[str] = Query(None)
    tags: Optional[str] = Query(None) # OR logic: match any of these tags, Will be comma seperated, must parse
    show_excluded: Optional[bool] = Query(False) # default false — excluded transactions are hidden
    date_from: Optional[str] = Query(None) # YYYY-MM-DD
    date_to: Optional[str] = Query(None) # YYYY-MM-DD
    sort_by: str = Field(default="date", pattern="^(date|amount)$") # date, amount, or description
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$") # asc or desc
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    model_config = incoming_config



class TransactionsPage(BaseModel): # Pydantic model for get transactions response with pagination metadata.
    data: list[Transaction]
    total: int
    page: int
    page_size: int
    has_next_page: bool

    model_config = outgoing_config


class TransactionUpdate(BaseModel):
    """
    Request body for PUT /transactions/{id}.
    Field names match exactly what the edit form sends (camelCase from the frontend).
    All fields are optional — only provided fields are written to the DB.
    """
    model_config = ConfigDict(extra="ignore")   # silently drop isFlagged and any other unknown fields

    date: Optional[date] = None             # → authorized_date
    description: Optional[str] = None
    merchant: Optional[str] = None          # → account_name
    amount: Optional[float] = None
    primaryCategory: Optional[str] = None   # → primary_category
    detailedCategory: Optional[str] = None  # → detailed_category
    isExcluded: Optional[bool] = None       # → exclude
    isRepayment: Optional[bool] = None      # → repayment
    notes: Optional[str] = None
    tags: Optional[list[str]] = None        # joined to comma-string in DB


class UploadJobResponse(BaseModel):
    job_id: str
    status: str

    model_config = outgoing_config


class ImportJobStatus(BaseModel):
    job_id: str
    status: str
    rows_imported: Optional[int] = None
    rows_updated: Optional[int] = None
    errors: Optional[str] = None

    model_config = outgoing_config