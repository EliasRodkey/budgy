#!python3
"""
backend.api.transactions.transactinos_models
Contains Pydantic models for transaction-related API endpoints, 
including request and response schemas for fetching transactions with optional month/year filters and pagination.
"""
# Standard library imports
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from pydantic.alias_generators import to_camel
from typing import Optional

# Third party imports
from fastapi import Query

# Local imports
from backend.utils.analysis_utils import PrimaryCategories, DetailedCategories


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
    posted_date: Optional[date] = None
    status: str
    account_name: Optional[str] = None
    description: str
    primary_category: str
    detailed_category: Optional[str] = None
    amount: Optional[float] = None # dollars (negative = expense)
    repayment: bool
    exclude: bool
    notes: Optional[str] = None # max 300 chars, edit modal only
    tags: list[str] = []

    model_config = outgoing_config

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [t.strip() for t in v.split(",") if t.strip()]
        return v



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

    @property
    def sort_ascending(self) -> bool:
        return self.sort_order != "desc"

    def to_db_filters(self) -> tuple[dict, list[str]]:
        """Returns (db_filters dict, tag_list) for use in db.query()."""
        db_filters: dict = {}

        if not self.show_excluded:
            db_filters["exclude"] = ("==", False)

        if self.primary_category in [e.value for e in PrimaryCategories]:
            db_filters["primary_category"] = ("==", self.primary_category)

        if self.detailed_category in [e.value for e in DetailedCategories]:
            db_filters["detailed_category"] = ("==", self.detailed_category)

        if self.date_from or self.date_to:
            date_from = self.date_from or "1900-01-01"
            date_to = self.date_to or datetime.now().strftime("%Y-%m-%d")
            db_filters["authorized_date"] = (
                "between",
                (
                    datetime.strptime(date_from, "%Y-%m-%d"),
                    datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59),
                ),
            )

        tag_list = [t.strip() for t in self.tags.split(",") if t.strip()] if self.tags else []
        return db_filters, tag_list



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
    All fields are optional — only provided fields are written to the DB.
    Accepts both camelCase aliases (from frontend) and snake_case field names.

    Note: the 'date' field (→ authorized_date) is intentionally absent here because
    naming a Pydantic field 'date' shadows the datetime.date type in its own annotation,
    causing Pydantic v2 to treat the type as NoneType. It is extracted manually in the
    endpoint before this model is validated.
    """
    model_config = ConfigDict(extra="ignore", alias_generator=to_camel, populate_by_name=True)

    description: Optional[str] = None
    account_name: Optional[str] = None      # editable account field (replaces merchant)
    amount: Optional[float] = None
    primaryCategory: Optional[str] = None   # → primary_category
    detailedCategory: Optional[str] = None  # → detailed_category
    isExcluded: Optional[bool] = None       # → exclude
    isRepayment: Optional[bool] = None      # → repayment
    notes: Optional[str] = None
    tags: Optional[list[str]] = None        # joined to comma-string in DB


class BulkUpdateRequest(BaseModel):
    """
    Request body for POST /transactions/bulk-update.
    Applies category and/or tag changes to a list of transaction IDs.
    """
    model_config = ConfigDict(extra="ignore")

    transaction_ids: list[int]
    primary_category: Optional[str] = None
    detailed_category: Optional[str] = None
    tags: Optional[list[str]] = None        # tags to ADD (merged with existing)
    exclude: Optional[bool] = None          # if set, mark matching transactions as excluded/included
    save_as_rule: bool = False              # if True, upsert a rule for the match pattern
    match_description: Optional[str] = None # required when save_as_rule=True
    match_account_name: Optional[str] = None # required when save_as_rule=True


class UploadJobResponse(BaseModel):
    job_id: str
    status: str

    model_config = outgoing_config


class ImportJobStatus(BaseModel):
    job_id: str
    status: str
    rows_imported: Optional[int] = None
    rows_updated: Optional[int] = None
    rows_skipped: Optional[int] = None
    skipped_rows: Optional[list[dict]] = None
    errors: Optional[str] = None
    rules_applied_from_cache: Optional[int] = None
    new_rules_saved: Optional[int] = None  # See note in UploadJobsTable.new_rules_saved

    model_config = outgoing_config