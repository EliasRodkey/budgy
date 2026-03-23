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

# Local imports
from budgy.database_modules.models.summaries import SummariesTable, summary_columns
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


# ─── TestCheckSummaryExists ───────────────────────────────────────────────────

class TestCheckSummaryExists:

    def test_returns_false_when_empty(self, clean_summaries_database):
        """_check_summary_exists returns False when the summaries table is empty."""
        summaries_manager, _ = clean_summaries_database
        assert summaries_manager._check_summary_exists(12, 2025) is False

    def test_returns_true_after_upload(self, full_transactions_database, clean_summaries_database):
        """_check_summary_exists returns True after a summary for that month/year is uploaded."""
        summaries_manager, _ = clean_summaries_database
        summary = full_transactions_database.generate_monthly_category_report(12, 2025)
        summaries_manager.upload_monthly_summary(12, 2025, summary)
        assert summaries_manager._check_summary_exists(12, 2025) is True

    def test_returns_false_for_different_month(self, full_transactions_database, clean_summaries_database):
        """_check_summary_exists returns False when the month doesn't match an uploaded record."""
        summaries_manager, _ = clean_summaries_database
        summary = full_transactions_database.generate_monthly_category_report(12, 2025)
        summaries_manager.upload_monthly_summary(12, 2025, summary)
        assert summaries_manager._check_summary_exists(11, 2025) is False

    def test_returns_false_for_different_year(self, full_transactions_database, clean_summaries_database):
        """_check_summary_exists returns False when the year doesn't match an uploaded record."""
        summaries_manager, _ = clean_summaries_database
        summary = full_transactions_database.generate_monthly_category_report(12, 2025)
        summaries_manager.upload_monthly_summary(12, 2025, summary)
        assert summaries_manager._check_summary_exists(12, 2024) is False

    def test_returns_bool(self, clean_summaries_database):
        """_check_summary_exists always returns a bool, not a list or None."""
        summaries_manager, _ = clean_summaries_database
        result = summaries_manager._check_summary_exists(1, 2024)
        assert isinstance(result, bool)


# ─── TestGetSummaryId ─────────────────────────────────────────────────────────

class TestGetSummaryId:

    def test_returns_integer_id_for_existing_record(self, full_transactions_database, clean_summaries_database):
        """_get_summary_id returns a positive integer id for a record that exists."""
        summaries_manager, _ = clean_summaries_database
        summary = full_transactions_database.generate_monthly_category_report(12, 2025)
        summaries_manager.upload_monthly_summary(12, 2025, summary)
        result_id = summaries_manager._get_summary_id(12, 2025)
        assert isinstance(result_id, int)
        assert result_id > 0

    def test_id_matches_fetched_record(self, full_transactions_database, clean_summaries_database):
        """The id returned by _get_summary_id matches the id stored on the fetched ORM record."""
        summaries_manager, _ = clean_summaries_database
        summary = full_transactions_database.generate_monthly_category_report(12, 2025)
        summaries_manager.upload_monthly_summary(12, 2025, summary)
        records = summaries_manager.fetch_items_by_attribute(month=12, year=2025)
        expected_id = records[0].id
        assert summaries_manager._get_summary_id(12, 2025) == expected_id


# ─── TestCleanMonthlySummary ──────────────────────────────────────────────────

class TestCleanMonthlySummary:

    def test_returns_dict(self):
        """_clean_monthly_summary returns a dict."""
        summary = _make_minimal_summary()
        result = test_summaries_manager._clean_monthly_summary(12, 2025, summary)
        assert isinstance(result, dict)

    def test_dict_contains_all_summary_column_keys(self):
        """Returned dict has a key for every column in summary_columns."""
        summary = _make_minimal_summary()
        result = test_summaries_manager._clean_monthly_summary(12, 2025, summary)
        expected_keys = {col.dest for col in summary_columns}
        assert expected_keys.issubset(result.keys()), (
            f"Missing keys: {expected_keys - result.keys()}"
        )

    def test_month_field_matches_arg(self):
        """month field in the returned dict matches the month argument."""
        summary = _make_minimal_summary()
        result = test_summaries_manager._clean_monthly_summary(6, 2024, summary)
        assert result[SummariesTable.month.name] == 6

    def test_year_field_matches_arg(self):
        """year field in the returned dict matches the year argument."""
        summary = _make_minimal_summary()
        result = test_summaries_manager._clean_monthly_summary(6, 2024, summary)
        assert result[SummariesTable.year.name] == 2024

    def test_date_field_is_first_of_month(self):
        """date field in the returned dict is datetime(year, month, 1)."""
        summary = _make_minimal_summary()
        result = test_summaries_manager._clean_monthly_summary(3, 2025, summary)
        assert isinstance(result[SummariesTable.date.name], datetime)
        assert result[SummariesTable.date.name] == datetime(2025, 3, 1)

    def test_float_columns_are_python_floats(self):
        """All category amount columns in the returned dict are Python floats."""
        summary = _make_minimal_summary()
        result = test_summaries_manager._clean_monthly_summary(12, 2025, summary)
        skip = {SummariesTable.date.name, SummariesTable.month.name, SummariesTable.year.name}
        for key, value in result.items():
            if key not in skip:
                assert isinstance(value, float), (
                    f"Expected float for '{key}', got {type(value).__name__} = {value!r}"
                )

    def test_missing_columns_default_to_zero(self):
        """Columns absent from the input summary are filled in as 0.0 in the output dict."""
        summary = _make_minimal_summary(income=500.0)
        result = test_summaries_manager._clean_monthly_summary(12, 2025, summary)
        # groceries not in input → should be 0.0
        assert result["groceries"] == 0.0
        assert result["food_and_drink"] == 0.0

    def test_raises_on_invalid_column_name(self):
        """Raises KeyError when input DataFrame has a column not in SummariesTable."""
        summary = pd.DataFrame({"not_a_real_column": [100.0]})
        with pytest.raises(KeyError):
            test_summaries_manager._clean_monthly_summary(12, 2025, summary)

    def test_raises_on_invalid_month_zero(self):
        """month=0 causes an error — datetime constructor raises ValueError before the assertion."""
        summary = _make_minimal_summary()
        with pytest.raises((AssertionError, ValueError)):
            test_summaries_manager._clean_monthly_summary(0, 2025, summary)

    def test_raises_on_invalid_month_thirteen(self):
        """month=13 causes an error — datetime constructor raises ValueError before the assertion."""
        summary = _make_minimal_summary()
        with pytest.raises((AssertionError, ValueError)):
            test_summaries_manager._clean_monthly_summary(13, 2025, summary)

    def test_raises_on_year_too_old(self):
        """year < 2000 raises AssertionError from the year validation check."""
        summary = _make_minimal_summary()
        with pytest.raises(AssertionError):
            test_summaries_manager._clean_monthly_summary(1, 1999, summary)

    def test_raises_on_future_year(self):
        """year beyond the current year raises AssertionError from the year validation check."""
        summary = _make_minimal_summary()
        future_year = datetime.now().year + 1
        with pytest.raises(AssertionError):
            test_summaries_manager._clean_monthly_summary(1, future_year, summary)

    def test_raises_on_negative_income(self):
        """Negative income value raises AssertionError from the income >= 0 check."""
        summary = _make_minimal_summary(income=-500.0)
        with pytest.raises(AssertionError):
            test_summaries_manager._clean_monthly_summary(12, 2025, summary)

    def test_real_report_cleans_without_error(self, full_transactions_database):
        """A real Dec 2025 report from generate_monthly_category_report cleans without raising."""
        summary = full_transactions_database.generate_monthly_category_report(12, 2025)
        result = test_summaries_manager._clean_monthly_summary(12, 2025, summary)
        assert isinstance(result, dict)
        assert result[SummariesTable.month.name] == 12
        assert result[SummariesTable.year.name] == 2025


# ─── TestUploadMonthlySummary ─────────────────────────────────────────────────

class TestUploadMonthlySummary:

    def test_upload_creates_record(self, full_transactions_database, clean_summaries_database):
        """Successful upload results in a record in the summaries table."""
        summaries_manager, _ = clean_summaries_database
        summary = full_transactions_database.generate_monthly_category_report(12, 2025)
        summaries_manager.upload_monthly_summary(12, 2025, summary)
        assert summaries_manager._check_summary_exists(12, 2025)

    def test_uploaded_record_has_correct_month_and_year(self, full_transactions_database, clean_summaries_database):
        """Uploaded summary record stores the correct month and year."""
        summaries_manager, _ = clean_summaries_database
        summary = full_transactions_database.generate_monthly_category_report(12, 2025)
        summaries_manager.upload_monthly_summary(12, 2025, summary)
        records = summaries_manager.fetch_items_by_attribute(month=12, year=2025)
        assert len(records) == 1
        assert records[0].month == 12
        assert records[0].year == 2025

    def test_upload_does_not_raise(self, full_transactions_database, clean_summaries_database):
        """upload_monthly_summary does not raise an exception on a clean first upload."""
        summaries_manager, _ = clean_summaries_database
        summary = full_transactions_database.generate_monthly_category_report(12, 2025)
        summaries_manager.upload_monthly_summary(12, 2025, summary)  # must not raise

    def test_duplicate_upload_logs_warning(self, full_transactions_database, clean_summaries_database, caplog):
        """Uploading the same month/year twice logs a warning about the duplicate."""
        summaries_manager, _ = clean_summaries_database
        summary = full_transactions_database.generate_monthly_category_report(12, 2025)
        summaries_manager.upload_monthly_summary(12, 2025, summary)
        with caplog.at_level(logging.WARNING, logger="budgy.database_modules.managers.summary_manager"):
            summaries_manager.upload_monthly_summary(12, 2025, summary)
        assert any("already exists" in msg for msg in caplog.messages), (
            f"Expected 'already exists' warning, got messages: {caplog.messages}"
        )

    def test_duplicate_upload_does_not_add_second_row(self, full_transactions_database, clean_summaries_database):
        """Uploading the same month/year twice leaves exactly one row in the table."""
        summaries_manager, _ = clean_summaries_database
        summary = full_transactions_database.generate_monthly_category_report(12, 2025)
        summaries_manager.upload_monthly_summary(12, 2025, summary)
        summaries_manager.upload_monthly_summary(12, 2025, summary)
        records = summaries_manager.fetch_items_by_attribute(month=12, year=2025)
        assert len(records) == 1

    def test_duplicate_upload_does_not_raise(self, full_transactions_database, clean_summaries_database):
        """A duplicate upload is silently skipped — no exception propagates to the caller."""
        summaries_manager, _ = clean_summaries_database
        summary = full_transactions_database.generate_monthly_category_report(12, 2025)
        summaries_manager.upload_monthly_summary(12, 2025, summary)
        # Second call must not raise even though the record already exists
        summaries_manager.upload_monthly_summary(12, 2025, summary)

    def test_different_months_upload_independently(self, full_transactions_database, clean_summaries_database):
        """Two different month/year pairs can each be uploaded as separate records."""
        summaries_manager, _ = clean_summaries_database
        summary_dec = full_transactions_database.generate_monthly_category_report(12, 2025)
        summary_nov = full_transactions_database.generate_monthly_category_report(11, 2025)
        summaries_manager.upload_monthly_summary(12, 2025, summary_dec)
        summaries_manager.upload_monthly_summary(11, 2025, summary_nov)
        assert summaries_manager._check_summary_exists(12, 2025)
        assert summaries_manager._check_summary_exists(11, 2025)


# ─── TestUpdateSummary ────────────────────────────────────────────────────────

class TestUpdateSummary:

    def test_update_logs_warning_when_summary_not_found(self, clean_summaries_database, caplog):
        """update_summary logs a warning when no record exists for the given month/year."""
        summaries_manager, _ = clean_summaries_database
        summary = _make_minimal_summary()
        with caplog.at_level(logging.WARNING, logger="budgy.database_modules.managers.summary_manager"):
            summaries_manager.update_summary(12, 2025, summary)
        assert any("doesn't exists" in msg or "doesn't exist" in msg for msg in caplog.messages), (
            f"Expected a 'doesn't exist' warning, got: {caplog.messages}"
        )

    def test_update_does_not_raise_when_not_found(self, clean_summaries_database):
        """update_summary does not raise when no matching record exists."""
        summaries_manager, _ = clean_summaries_database
        summary = _make_minimal_summary()
        summaries_manager.update_summary(12, 2025, summary)  # must not raise

    def test_update_does_not_raise_when_record_exists(self, full_transactions_database, clean_summaries_database):
        """update_summary does not raise when called for an existing month/year record."""
        summaries_manager, _ = clean_summaries_database
        summary = full_transactions_database.generate_monthly_category_report(12, 2025)
        summaries_manager.upload_monthly_summary(12, 2025, summary)
        summary["income"] = 10000
        summaries_manager.update_summary(12, 2025, summary)  # must not raise

    def test_update_does_not_warn_when_record_exists(self, full_transactions_database, clean_summaries_database, caplog):
        """update_summary does not log a 'doesn't exist' warning when the record is present."""
        summaries_manager, _ = clean_summaries_database
        summary = full_transactions_database.generate_monthly_category_report(12, 2025)
        summaries_manager.upload_monthly_summary(12, 2025, summary)
        caplog.clear()
        with caplog.at_level(logging.WARNING, logger="budgy.database_modules.managers.summary_manager"):
            summaries_manager.update_summary(12, 2025, summary)
        assert not any("doesn't exists" in msg or "doesn't exist" in msg for msg in caplog.messages)
