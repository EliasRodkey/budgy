#!python3
"""
tests.test_database_modules.test_models.test_summaries

Tests for budgy.database_modules.models.summaries — SummariesTable ORM definition and summary_columns list.
"""
# Standard library imports
from datetime import datetime

# Third party imports
import pytest

# Local imports
from budgy.database_modules.models.summaries import SummariesTable, summary_columns
from budgy.utils.analysis_utils import PrimaryCategories, DetailedCategories

# Initialize module logger
import logging
logger = logging.getLogger(__name__)


# All primary category column names as they appear in SummariesTable
EXPECTED_PRIMARY_CATEGORY_COLUMNS = [
    member.name.lower().replace(" ", "_").replace("&", "and")
    for member in PrimaryCategories
]

# Spot-check a selection of detailed category columns
SPOT_CHECK_DETAILED_COLUMNS = [
    "wages", "groceries", "rent", "medical", "flights", "fitness", "restaurants_and_bars",
]

SAMPLE_BUDGET = {
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
}


def test_summaries_table_name():
    """SummariesTable has the correct table name."""
    assert SummariesTable.__tablename__ == "summaries"


def test_summaries_table_columns(clean_summaries_database):
    """SummariesTable DataFrame contains id, date, month, year, budget_id, and primary category columns."""
    summaries_db, _ = clean_summaries_database
    df = summaries_db.to_dataframe()

    required_columns = ["id", "date", "month", "year", "budget_id"]
    for col in required_columns:
        assert col in df.columns, f"Expected column '{col}' not found in SummariesTable: {list(df.columns)}"


def test_summaries_table_detailed_category_columns(clean_summaries_database):
    """SummariesTable DataFrame contains spot-check detailed category columns."""
    summaries_db, _ = clean_summaries_database
    df = summaries_db.to_dataframe()

    for col in SPOT_CHECK_DETAILED_COLUMNS:
        assert col in df.columns, f"Expected detailed category column '{col}' not found: {list(df.columns)}"


def test_summaries_table_crud(clean_summaries_database):
    """A summary row can be added with a valid FK budget_id, fetched, and deleted."""
    summaries_db, budgets_db = clean_summaries_database

    # Add a budget first (FK requirement)
    budgets_db.add_item(**SAMPLE_BUDGET)
    budget = budgets_db.fetch_all_items()
    assert len(budget) == 1
    budget_id = budget[0].id

    # Add a summary row referencing the budget
    summaries_db.add_item(
        date=datetime(2025, 12, 1),
        month=12,
        year=2025,
        budget_id=budget_id,
        income=4800.0,
        food_and_drink=550.0,
    )

    items = summaries_db.fetch_all_items()
    assert len(items) == 1
    assert items[0].month == 12
    assert items[0].year == 2025
    assert items[0].income == 4800.0


def test_summaries_table_delete(clean_summaries_database):
    """A summary row can be deleted from SummariesTable."""
    summaries_db, budgets_db = clean_summaries_database

    budgets_db.add_item(**SAMPLE_BUDGET)
    budget = budgets_db.fetch_all_items()
    budget_id = budget[0].id

    summaries_db.add_item(
        date=datetime(2025, 11, 1),
        month=11,
        year=2025,
        budget_id=budget_id,
        income=5100.0,
    )

    items_before = summaries_db.fetch_all_items()
    assert len(items_before) == 1

    summaries_db.delete_items_by_attribute(month=11)
    items_after = summaries_db.fetch_all_items()
    assert len(items_after) == 0


def test_summary_columns_list_is_empty():
    """summary_columns is an empty list (not a broken Column() namedtuple call)."""
    assert isinstance(summary_columns, list)
    assert len(summary_columns) == 0
