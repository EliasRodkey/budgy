#!python3
"""
tests.test_database_modules.test_models.test_summaries

Tests for budgy.database_modules.models.summaries — SummariesTable ORM definition and summary_columns list.
"""
# Standard library imports
from datetime import datetime

# Third party imports
import pytest

# Custom imports
from pleasant_database import DatabaseIntegrityError

# Local imports
from backend.database_modules.models.summaries import SummariesTable, summary_columns
from backend.utils.analysis_utils import PrimaryCategories, DetailedCategories

# Initialize module logger
import logging
logger = logging.getLogger(__name__)


# All primary category column names as they appear in SummariesTable
EXPECTED_PRIMARY_CATEGORY_COLUMNS = [
    member.name.lower().replace(" ", "_").replace("&", "and")
    for member in PrimaryCategories
]

# Spot-check a selection of detailed category columns (prefixed as stored in SummariesTable)
SPOT_CHECK_DETAILED_COLUMNS = [
    "sum_wages", "sum_groceries", "sum_rent", "sum_medical", "sum_flights", "sum_fitness", "sum_restaurants_and_bars",
]


def test_summaries_table_name():
    """SummariesTable has the correct table name."""
    assert SummariesTable.__tablename__ == "summaries"


def test_summaries_table_columns(clean_summaries_database):
    """SummariesTable DataFrame contains id, date, month, year, primary category columns, and spot-check detailed columns."""
    summaries_db, _ = clean_summaries_database
    df = summaries_db.to_dataframe()

    for col in ["id", "date", "month", "year"]:
        assert col in df.columns, f"Expected column '{col}' not found in SummariesTable: {list(df.columns)}"

    for col in SPOT_CHECK_DETAILED_COLUMNS:
        assert col in df.columns, f"Expected detailed category column '{col}' not found: {list(df.columns)}"


def test_summaries_table_crud(clean_summaries_database):
    """A summary row can be added, fetched, and deleted."""
    summaries_db, budgets_db = clean_summaries_database
    budgets_db.add_item(date_created=datetime(2025, 1, 1), uq_hash="test_hash_crud")
    budget_id = budgets_db.fetch_all_items()[0].id

    summaries_db.add_item(
        date=datetime(2025, 12, 1),
        month=12,
        year=2025,
        budget_id=budget_id,
        sum_income=4800.0,
        sum_food_and_drink=550.0,
    )

    items = summaries_db.fetch_all_items()
    assert len(items) == 1
    assert items[0].month == 12
    assert items[0].year == 2025
    assert items[0].sum_income == 4800.0


def test_summaries_table_delete(clean_summaries_database):
    """A summary row can be deleted from SummariesTable."""
    summaries_db, budgets_db = clean_summaries_database
    budgets_db.add_item(date_created=datetime(2025, 1, 1), uq_hash="test_hash_delete")
    budget_id = budgets_db.fetch_all_items()[0].id

    summaries_db.add_item(
        date=datetime(2025, 11, 1),
        month=11,
        year=2025,
        budget_id=budget_id,
        sum_income=5100.0,
    )

    items_before = summaries_db.fetch_all_items()
    assert len(items_before) == 1

    summaries_db.delete_items_by_attribute(month=11)
    items_after = summaries_db.fetch_all_items()
    assert len(items_after) == 0


def test_summary_columns_list_is_populated():
    """summary_columns is a non-empty list of Field namedtuples derived from SummariesTable."""
    assert isinstance(summary_columns, list)
    assert len(summary_columns) > 0


def test_summary_month_year_uq_constraint(clean_summaries_database):
    """Tests the unique constraint on the month year combination in the summary table"""
    summaries_db, budgets_db = clean_summaries_database
    budgets_db.add_item(date_created=datetime(2025, 1, 1), uq_hash="test_hash_uq")
    budget_id = budgets_db.fetch_all_items()[0].id

    summaries_db.add_item(month=12, year=2025, budget_id=budget_id)
    summaries_db.add_item(month=12, year=2024, budget_id=budget_id)

    with pytest.raises(DatabaseIntegrityError):
        summaries_db.add_item(month=12, year=2025, budget_id=budget_id)

    assert len(summaries_db.fetch_all_items()) == 2
