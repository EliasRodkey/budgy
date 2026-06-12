#!python3
"""
backend.api.rules.rules_models
Pydantic models and serialization helpers for the transaction rules API.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

_camel_config = ConfigDict(
    alias_generator=to_camel,
    populate_by_name=True,
)


# ─── Response models ──────────────────────────────────────────────────────────

class RuleResponse(BaseModel):
    model_config = _camel_config

    id: int
    match_description: str
    match_account_name: str
    primary_category: Optional[str] = None
    detailed_category: Optional[str] = None
    tags: list[str] = []
    exclude: Optional[bool] = None
    created_at: datetime
    updated_at: datetime


# ─── Request models ───────────────────────────────────────────────────────────

class RuleCreate(BaseModel):
    model_config = _camel_config

    match_description: str
    match_account_name: str
    primary_category: Optional[str] = None
    detailed_category: Optional[str] = None
    exclude: Optional[bool] = None


class RuleUpdate(BaseModel):
    model_config = _camel_config

    match_description: str
    match_account_name: str
    primary_category: Optional[str] = None
    detailed_category: Optional[str] = None
    exclude: Optional[bool] = None


# ─── Serialization helpers ────────────────────────────────────────────────────

def db_row_to_rule_response(row) -> RuleResponse:
    """Convert a TransactionRulesTable ORM row to a RuleResponse."""
    tags = [t.strip() for t in (row.tags or "").split(",") if t.strip()]
    return RuleResponse(
        id=row.id,
        match_description=row.match_description,
        match_account_name=row.match_account_name,
        primary_category=row.primary_category,
        detailed_category=row.detailed_category,
        tags=tags,
        exclude=row.exclude,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
