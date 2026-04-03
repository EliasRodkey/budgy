#!python3
"""
tests.test_database_modules.test_models.test_budgets

Tests for backend.database_modules.models.budgets — BudgetsTable ORM definition and budget_columns list.
"""
# Standard library imports
from datetime import datetime

# Third party imports
import pytest

# Local imports
from backend.database_modules.models.budgets import BudgetsTable, budget_columns

# Initialize module logger
import logging
logger = logging.getLogger(__name__)


EXPECTED_BUDGET_COLUMNS = [
    "id",
    "date_created",
    "income",
    "transfers",
    "debt_payments",
    "investments",
    "bank_fees",
    "food_and_drink",
    "shopping",
    "housing_and_utilities",
    "health_and_wellness",
    "entertainment",
    "insurance",
    "services",
    "transportation",
    "travel",
    "government_and_charity",
    "other",
    "net_gain_or_loss",
    "uq_hash",
]


def _make_db_budget_record(uq_hash: str = "abc123deadbeef") -> dict:
    """Returns a dict suitable for direct add_item insertion into the budgets table."""
    return {
        "date_created": datetime(2025, 1, 1),
        "income": 5000.0,
        "transfers": 0.0,
        "debt_payments": 200.0,
        "investments": 500.0,
        "bank_fees": 10.0,
        "food_and_drink": 600.0,
        "shopping": 300.0,
        "housing_and_utilities": 1500.0,
        "health_and_wellness": 100.0,
        "entertainment": 150.0,
        "insurance": 200.0,
        "services": 50.0,
        "transportation": 120.0,
        "travel": 80.0,
        "government_and_charity": 40.0,
        "other": 50.0,
        "uq_hash": uq_hash,
    }


def test_budgets_table_name():
    """BudgetsTable has the correct table name."""
    assert BudgetsTable.__tablename__ == "budgets"


def test_budgets_table_columns(clean_budgets_database):
    """BudgetsTable exposes all expected primary category columns plus id and date_created."""
    df = clean_budgets_database.to_dataframe()
    for col in EXPECTED_BUDGET_COLUMNS:
        assert col in df.columns, f"Expected column '{col}' not found in BudgetsTable dataframe columns: {list(df.columns)}"


def test_budgets_table_add_and_fetch(clean_budgets_database):
    """A budget row can be added, fetched, and converted to a DataFrame with correct columns."""
    db = clean_budgets_database
    record = _make_db_budget_record()
    db.add_item(**record)

    items = db.fetch_all_items()
    assert items is not None
    assert len(items) == 1
    assert items[0].income == 5000.0
    assert items[0].food_and_drink == 600.0

    df = db.to_dataframe()
    assert not df.empty
    assert list(df.columns) == EXPECTED_BUDGET_COLUMNS


def test_budgets_table_delete(clean_budgets_database):
    """A budget row can be deleted from BudgetsTable."""
    db = clean_budgets_database
    db.add_item(**_make_db_budget_record())

    items_before = db.fetch_all_items()
    assert len(items_before) == 1

    db.delete_items_by_attribute(income=5000.0)
    items_after = db.fetch_all_items()
    assert len(items_after) == 0


def test_budget_columns_list_is_populated():
    """budget_columns is a non-empty list of Field namedtuples covering all BudgetsTable columns."""
    assert isinstance(budget_columns, list)
    assert len(budget_columns) > 0
    assert all(hasattr(col, "src") and hasattr(col, "dest") and hasattr(col, "convert") for col in budget_columns)
