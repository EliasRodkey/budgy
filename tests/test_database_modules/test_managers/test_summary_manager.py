#!python3
"""
tests.test_database_modules.test_managers.test_summary_manager.py

Tests for budgy.database_modules.managers.summary_manager.py — SummariesTableManager.

Input data for upload/update functions is generated via TransactionsTableManager.generate_monthly_category_report.
"""
# Standard library imports
from datetime import datetime

# Third party imports
import pandas as pd
import pytest

# Custom imports
from pleasant_database import ItemNotFoundError

# Local imports
from budgy.database_modules.models.budgets import BudgetsTable
from budgy.database_modules.models.summaries import SummariesTable, summary_columns
from budgy.utils.analysis_utils import PrimaryCategories
from tests.conftest import (
    test_summaries_manager,
    full_transactions_database,
    clean_summaries_database,
)

# Initialize module logger
import logging
logger = logging.getLogger(__name__)


# ─── helpers ─────────────────────────────────────────────────────────────────

def _make_minimal_summary(income: float = 1000.0) -> pd.DataFrame:
    """Returns a minimal one-row DataFrame with a valid income column."""
    return pd.DataFrame({"income": [float(income)]})


def _make_db_budget_record(uq_hash: str = "testhash1") -> dict:
    """Returns a dict suitable for direct add_item insertion into the budgets table."""
    base = {cat: 0.0 for cat in PrimaryCategories.as_snake_case_headers()}
    base["uq_hash"] = uq_hash
    base["date_created"] = datetime(2024, 1, 1)
    return base


def _make_db_summary_record(month: int, year: int, budget_id: int) -> dict:
    """Returns a dict suitable for direct add_item insertion into the summaries table."""
    non_scalar = {"date", "month", "year", "budget_id"}
    record = {col.dest: 0.0 for col in summary_columns if col.dest not in non_scalar}
    record["date"] = datetime(year, month, 1)
    record["month"] = month
    record["year"] = year
    record["budget_id"] = budget_id
    record["income"] = 1000.0
    return record


# ─── TestCheckSummaryExists ───────────────────────────────────────────────────

class TestCheckSummaryExists:

    def test_returns_false_and_is_bool_when_empty(self, clean_summaries_database):
        """_check_summary_exists returns False (and a bool) when the summaries table is empty."""
        summaries_manager, _ = clean_summaries_database
        result = summaries_manager._check_summary_exists(12, 2025)
        assert result is False
        assert isinstance(result, bool)

    def test_with_seeded_record(self, clean_summaries_database):
        """True for the seeded month/year; False for a different month or year."""
        summaries_manager, budgets_manager = clean_summaries_database
        budgets_manager.add_item(**_make_db_budget_record())
        budget_id = budgets_manager.fetch_all_items()[0].id
        summaries_manager.add_item(**_make_db_summary_record(12, 2025, budget_id))

        assert summaries_manager._check_summary_exists(12, 2025) is True
        assert summaries_manager._check_summary_exists(11, 2025) is False
        assert summaries_manager._check_summary_exists(12, 2024) is False


# ─── TestGetSummaryId ─────────────────────────────────────────────────────────

class TestGetSummaryId:

    def test_returns_correct_id(self, clean_summaries_database):
        """_get_summary_id returns a positive int matching the stored record's id."""
        summaries_manager, budgets_manager = clean_summaries_database
        budgets_manager.add_item(**_make_db_budget_record())
        budget_id = budgets_manager.fetch_all_items()[0].id
        summaries_manager.add_item(**_make_db_summary_record(12, 2025, budget_id))

        expected_id = summaries_manager.fetch_items_by_attribute(month=12, year=2025)[0].id
        result = summaries_manager._get_summary_id(12, 2025)

        assert isinstance(result, int)
        assert result > 0
        assert result == expected_id

    def test_raises_when_not_found(self, clean_summaries_database):
        """_get_summary_id raises ItemNotFoundError when no record exists for the given month/year."""
        summaries_manager, _ = clean_summaries_database
        with pytest.raises(ItemNotFoundError):
            summaries_manager._get_summary_id(12, 2025)


# ─── TestCleanMonthlySummary ──────────────────────────────────────────────────

class TestCleanMonthlySummary:

    def test_output_shape_and_types(self):
        """Returns a dict with all summary_columns keys; floats for category columns; missing columns default to 0.0."""
        summary = _make_minimal_summary()
        result = test_summaries_manager._clean_monthly_summary(12, 2025, summary, budget_id=1)

        assert isinstance(result, dict)
        assert {col.dest for col in summary_columns}.issubset(result.keys())

        skip = {SummariesTable.date.name, SummariesTable.month.name,
                SummariesTable.year.name, SummariesTable.budget_id.name}
        for key, value in result.items():
            if key not in skip:
                assert isinstance(value, float), (
                    f"Expected float for '{key}', got {type(value).__name__} = {value!r}"
                )

        assert result["groceries"] == 0.0
        assert result["food_and_drink"] == 0.0

    def test_date_fields_match_args(self):
        """month, year, and date fields in the returned dict match the arguments."""
        summary = _make_minimal_summary()
        result = test_summaries_manager._clean_monthly_summary(6, 2024, summary, budget_id=1)

        assert result[SummariesTable.month.name] == 6
        assert result[SummariesTable.year.name] == 2024
        assert isinstance(result[SummariesTable.date.name], datetime)
        assert result[SummariesTable.date.name] == datetime(2024, 6, 1)

    def test_raises_on_invalid_column_name(self):
        """Raises KeyError when input DataFrame has a column not in SummariesTable."""
        summary = pd.DataFrame({"not_a_real_column": [100.0]})
        with pytest.raises(KeyError):
            test_summaries_manager._clean_monthly_summary(12, 2025, summary, budget_id=1)

    def test_raises_on_invalid_month(self):
        """month=0 and month=13 both raise (datetime constructor or assertion)."""
        summary = _make_minimal_summary()
        with pytest.raises((AssertionError, ValueError)):
            test_summaries_manager._clean_monthly_summary(0, 2025, summary, budget_id=1)
        with pytest.raises((AssertionError, ValueError)):
            test_summaries_manager._clean_monthly_summary(13, 2025, summary, budget_id=1)

    def test_raises_on_invalid_year(self):
        """year < 2000 and year > current year both raise AssertionError."""
        summary = _make_minimal_summary()
        with pytest.raises(AssertionError):
            test_summaries_manager._clean_monthly_summary(1, 1999, summary, budget_id=1)
        with pytest.raises(AssertionError):
            test_summaries_manager._clean_monthly_summary(1, datetime.now().year + 1, summary, budget_id=1)

    def test_raises_on_negative_income(self):
        """Negative income value raises AssertionError from the income >= 0 check."""
        summary = _make_minimal_summary(income=-500.0)
        with pytest.raises(AssertionError):
            test_summaries_manager._clean_monthly_summary(12, 2025, summary, budget_id=1)

    def test_real_report_cleans_without_error(self, full_transactions_database):
        """A real Dec 2025 report from generate_monthly_category_report cleans without raising."""
        summary = full_transactions_database.generate_monthly_category_report(12, 2025)
        result = test_summaries_manager._clean_monthly_summary(12, 2025, summary, budget_id=1)
        assert isinstance(result, dict)
        assert result[SummariesTable.month.name] == 12
        assert result[SummariesTable.year.name] == 2025

    def test_budget_id_in_result_when_provided(self):
        """Explicit budget_id argument appears in the returned dict."""
        summary = _make_minimal_summary()
        result = test_summaries_manager._clean_monthly_summary(12, 2025, summary, budget_id=42)
        assert result[SummariesTable.budget_id.name] == 42

    def test_budget_id_from_latest_when_omitted(self, clean_summaries_database):
        """When budget_id is omitted, result uses the budget_id from the most recently inserted summary."""
        summaries_manager, budgets_manager = clean_summaries_database
        budgets_manager.add_item(**_make_db_budget_record())
        budget_id = budgets_manager.fetch_all_items()[0].id
        summaries_manager.add_item(**_make_db_summary_record(11, 2025, budget_id))

        result = summaries_manager._clean_monthly_summary(12, 2025, _make_minimal_summary())
        assert result[SummariesTable.budget_id.name] == budget_id


# ─── TestUploadMonthlySummary ─────────────────────────────────────────────────

class TestUploadMonthlySummary:

    def test_upload_creates_record(self, full_transactions_database, clean_summaries_database):
        """Successful upload inserts one record and does not raise."""
        summaries_manager, budgets_manager = clean_summaries_database
        budgets_manager.add_item(**_make_db_budget_record())
        budget_id = budgets_manager.fetch_all_items()[0].id

        summary = full_transactions_database.generate_monthly_category_report(12, 2025)
        summaries_manager.upload_monthly_summary(12, 2025, summary, budget_id=budget_id)

        assert summaries_manager._check_summary_exists(12, 2025)
        records = summaries_manager.fetch_items_by_attribute(month=12, year=2025)
        assert len(records) == 1
        assert records[0].month == 12
        assert records[0].year == 2025

    def test_duplicate_upload_behavior(self, full_transactions_database, clean_summaries_database, caplog):
        """A duplicate upload is silently skipped: no exception, warning logged, exactly one row remains."""
        summaries_manager, budgets_manager = clean_summaries_database
        budgets_manager.add_item(**_make_db_budget_record())
        budget_id = budgets_manager.fetch_all_items()[0].id

        summary = full_transactions_database.generate_monthly_category_report(12, 2025)
        summaries_manager.upload_monthly_summary(12, 2025, summary, budget_id=budget_id)

        with caplog.at_level(logging.WARNING, logger="budgy.database_modules.managers.summary_manager"):
            summaries_manager.upload_monthly_summary(12, 2025, summary, budget_id=budget_id)

        assert any("already exists" in msg for msg in caplog.messages)
        assert len(summaries_manager.fetch_items_by_attribute(month=12, year=2025)) == 1

    def test_different_months_upload_independently(self, full_transactions_database, clean_summaries_database):
        """Two different month/year pairs each produce a separate record."""
        summaries_manager, budgets_manager = clean_summaries_database
        budgets_manager.add_item(**_make_db_budget_record())
        budget_id = budgets_manager.fetch_all_items()[0].id

        summaries_manager.upload_monthly_summary(
            12, 2025, full_transactions_database.generate_monthly_category_report(12, 2025), budget_id=budget_id
        )
        summaries_manager.upload_monthly_summary(
            11, 2025, full_transactions_database.generate_monthly_category_report(11, 2025), budget_id=budget_id
        )

        assert summaries_manager._check_summary_exists(12, 2025)
        assert summaries_manager._check_summary_exists(11, 2025)

    def test_uploaded_record_budget_id(self, clean_summaries_database):
        """Uploaded record stores the explicit budget_id and that id resolves to a real budget row."""
        summaries_manager, budgets_manager = clean_summaries_database
        budgets_manager.add_item(**_make_db_budget_record())
        budget_id = budgets_manager.fetch_all_items()[0].id

        summaries_manager.upload_monthly_summary(12, 2025, _make_minimal_summary(), budget_id=budget_id)

        record = summaries_manager.fetch_items_by_attribute(month=12, year=2025)[0]
        assert record.budget_id == budget_id
        fetched_budget = budgets_manager.fetch_budget_by_id(record.budget_id)
        assert fetched_budget is not BudgetsTable
        assert fetched_budget.id == budget_id

    def test_uploaded_record_inherits_latest_budget_when_omitted(self, clean_summaries_database):
        """When budget_id is omitted, the uploaded record inherits from the most recently inserted summary."""
        summaries_manager, budgets_manager = clean_summaries_database
        budgets_manager.add_item(**_make_db_budget_record())
        budget_id = budgets_manager.fetch_all_items()[0].id
        summaries_manager.add_item(**_make_db_summary_record(11, 2025, budget_id))

        summaries_manager.upload_monthly_summary(12, 2025, _make_minimal_summary())

        record = summaries_manager.fetch_items_by_attribute(month=12, year=2025)[0]
        assert record.budget_id == budget_id


# ─── TestUpdateSummary ────────────────────────────────────────────────────────

class TestUpdateSummary:

    def test_update_when_record_missing(self, clean_summaries_database, caplog):
        """update_summary logs a warning and does not raise when no record exists."""
        summaries_manager, _ = clean_summaries_database
        with caplog.at_level(logging.WARNING, logger="budgy.database_modules.managers.summary_manager"):
            summaries_manager.update_summary(12, 2025, _make_minimal_summary())
        assert any("doesn't exists" in msg or "doesn't exist" in msg for msg in caplog.messages)

    def test_update_when_record_exists(self, full_transactions_database, clean_summaries_database, caplog):
        """update_summary does not raise and does not warn when the record is present."""
        summaries_manager, budgets_manager = clean_summaries_database
        budgets_manager.add_item(**_make_db_budget_record())
        budget_id = budgets_manager.fetch_all_items()[0].id

        summary = full_transactions_database.generate_monthly_category_report(12, 2025)
        summaries_manager.upload_monthly_summary(12, 2025, summary, budget_id=budget_id)

        summary["income"] = 10000
        caplog.clear()
        with caplog.at_level(logging.WARNING, logger="budgy.database_modules.managers.summary_manager"):
            summaries_manager.update_summary(12, 2025, summary)

        assert not any("doesn't exists" in msg or "doesn't exist" in msg for msg in caplog.messages)


# ─── TestGetLatestBudgetId ────────────────────────────────────────────────────

class TestGetLatestBudgetId:

    def test_returns_most_recently_inserted_budget_id(self, clean_summaries_database):
        """Returns the budget_id of the summary with the highest id (most recently inserted); result is an int."""
        summaries_manager, budgets_manager = clean_summaries_database
        budgets_manager.add_item(**_make_db_budget_record(uq_hash="hash_a"))
        budgets_manager.add_item(**_make_db_budget_record(uq_hash="hash_b"))
        budget_a_id, budget_b_id = [b.id for b in sorted(budgets_manager.fetch_all_items(), key=lambda b: b.id)]

        summaries_manager.add_item(**_make_db_summary_record(10, 2025, budget_a_id))
        summaries_manager.add_item(**_make_db_summary_record(11, 2025, budget_b_id))

        result = summaries_manager._get_latest_budget_id()
        assert result == budget_b_id
        assert isinstance(result, int)

    def test_raises_when_table_empty(self, clean_summaries_database):
        """Raises ItemNotFoundError when the summaries table is empty."""
        summaries_manager, _ = clean_summaries_database
        with pytest.raises(ItemNotFoundError):
            summaries_manager._get_latest_budget_id()
