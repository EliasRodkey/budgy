#!python3
"""
backend.database_modules.models.rules.py -
ORM table definition for transaction categorization/tagging rules.

Classes:
    - TransactionRulesTable: Stores rules that map (description, account_name) pairs
      to categories and/or tags. Applied automatically after CSV uploads.
"""
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from pleasant_database import BaseTable

from pleasant_loggers import get_logger
logger = get_logger(__name__)


class TransactionRulesTable(BaseTable):
    """
    Stores user-defined rules that associate a (description, account_name) pair
    with a primary_category, detailed_category, and/or tags.

    Rules are applied automatically when new CSV files are imported, and are
    created/updated when the user bulk-applies a category or tag change via the UI.

    Database Structure:
        table name: transaction_rules
    Columns:
        - id: Integer, Primary Key, Auto Increment
        - match_description: String — exact description to match
        - match_account_name: String — exact account_name to match
        - match_type: String — matching strategy; currently always "exact"
        - primary_category: String (nullable) — primary category to apply
        - detailed_category: String (nullable) — detailed category to apply
        - tags: String (nullable) — comma-separated tags to apply
        - created_at: DateTime
        - updated_at: DateTime
    Constraints:
        - UNIQUE (match_description, match_account_name) — one rule per pattern
    """

    __tablename__ = "transaction_rules"

    __table_args__ = (
        UniqueConstraint("match_description", "match_account_name", name="uq_rule_pattern"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_description = Column(String, nullable=False)
    match_account_name = Column(String, nullable=False)
    match_type = Column(String, nullable=False, default="exact")
    primary_category = Column(String, nullable=True)
    detailed_category = Column(String, nullable=True)
    tags = Column(String, nullable=True)  # comma-separated
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
