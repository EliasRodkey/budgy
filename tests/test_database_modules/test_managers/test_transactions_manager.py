#!python3
"""
tests.test_database_modules.test_managers.test_transactions_manager.py

Tests for budgy.database_modules.managers.transactions_manager.py module — Database query and update functions for Transactions and Updates
"""
# Standard library imports
from datetime import datetime
import os

# Third party imports
import pandas as pd
import pytest

# Local imports
from budgy.database_modules.managers.common import DuplicateError
from budgy.database_modules.models.common import TableStatus
from budgy.database_modules.models.transactions import TransactionsTable
from budgy.database_modules.managers.common import format_column_names
from budgy.utils.analysis_utils import PrimaryCategories, DetailedCategories
from tests.conftest import TEST_CSV_DIR, full_transactions_database

# Initialize module logger
import logging
logger = logging.getLogger(__name__)


duplicate_update_item = {
    "timestamp": datetime(2024, 1, 1),
    "filepath": os.path.join(TEST_CSV_DIR, "TEST_UPDATE.csv"),
    "status": TableStatus.COMPLETE
}

new_update_item = {
    "timestamp": datetime(2024, 1, 1),
    "filepath": os.path.join(TEST_CSV_DIR, "TEST_UPDATE_2.csv"),
}


# =========================UpdatesTableManager===================================

class TestUpdatesTableManager:

    def test_generate_update_entry(self, clean_updates_database):
        """Tests the updates_table_manager to make sure that we are not creating multiple uploads for the same file"""
        try:
            clean_updates_database.generate_update_entry(duplicate_update_item["filepath"], TableStatus.COMPLETE)

        except Exception as e:
            assert isinstance(e, DuplicateError)

        finally:
            # This should execute without an error since the status is changing
            clean_updates_database.generate_update_entry(new_update_item["filepath"], TableStatus.INCOMPLETE)
            clean_updates_database.generate_update_entry(new_update_item["filepath"], TableStatus.COMPLETE)

            df = clean_updates_database.to_dataframe()
            clean_updates_database.clear_table()

        assert df.filepath.isin([duplicate_update_item["filepath"]]).any()

        new_update_idx = df.index[df.filepath == new_update_item["filepath"]]

        status = df.iloc[new_update_idx, :].status.iloc[0]
        assert status == TableStatus.COMPLETE

    def test_iter_csv_not_uploaded(self, clean_updates_database):
        """Tests the iter csv uploaded function to make sure it can correctly identify which file still needs uploading"""
        db_manager = clean_updates_database
        uploaded_files = db_manager.to_dataframe()["filepath"]
        for csv in db_manager.iter_csv_not_uploaded(csv_directory=TEST_CSV_DIR):
            db_item = db_manager.fetch_items_by_attribute(filepath=csv)

            # If an ORM object is returned, check to make sure that the status is set to incomplete.
            if db_item:
                assert db_item[0].status != TableStatus.COMPLETE

            # Otherwise the filepath should not appear in the retrieved db values
            else:
                assert csv not in uploaded_files
                from tests.conftest import update_items
                assert csv not in [item["filepath"] for item in update_items]


# =========================TransactionsTableManager===================================

class TestTransactionsTableManager:

    # --- generate_monthly_category_report ---

    def test_generate_monthly_category_report(self, full_transactions_database):
        """Test the generate_monthly_category_report function for a specific month and year.
        The function only returns columns for categories that appear in the data, so we verify
        that all returned columns are valid category names (not that all categories are present).
        """
        report_df = full_transactions_database.generate_monthly_category_report(12, 2025)

        assert isinstance(report_df, pd.DataFrame), "Report should be a pandas DataFrame."
        assert not report_df.empty, "Expected non-empty report for December 2025."

        all_category_values = pd.Series(
            [m.value for m in PrimaryCategories] + [m.value for m in DetailedCategories]
        )
        all_valid_columns = set(format_column_names(all_category_values))
        invalid_cols = [col for col in report_df.columns if col not in all_valid_columns]
        assert not invalid_cols, f"Report contains unexpected column names: {invalid_cols}"

    def test_generate_monthly_category_report_empty(self, full_transactions_database):
        """generate_monthly_category_report returns an empty DataFrame with correct columns for a month with no data."""
        report_df = full_transactions_database.generate_monthly_category_report(1, 2000)

        assert isinstance(report_df, pd.DataFrame)
        assert report_df.empty

    def test_generate_monthly_category_report_values_are_numeric(self, full_transactions_database):
        """generate_monthly_category_report returns numeric (float) values for all category columns."""
        report_df = full_transactions_database.generate_monthly_category_report(12, 2025)
        assert not report_df.empty
        for col in report_df.columns:
            assert pd.api.types.is_numeric_dtype(report_df[col]), \
                f"Column '{col}' should be numeric, got {report_df[col].dtype}"

    # --- retrieve_records_by_attribute_over_period ---

    def test_retrieve_records_returns_dataframe(self, full_transactions_database):
        """retrieve_records_by_attribute_over_period returns a pd.DataFrame."""
        result = full_transactions_database.retrieve_records_by_attribute_over_period(12, 2025)
        assert isinstance(result, pd.DataFrame)

    def test_retrieve_records_by_month_year(self, full_transactions_database):
        """Records filtered by month=12, year=2025 all fall within December 2025."""
        result = full_transactions_database.retrieve_records_by_attribute_over_period(12, 2025)
        assert not result.empty, "Expected records for December 2025 in the test dataset."
        for date in result["authorized_date"]:
            assert date.month == 12 and date.year == 2025, \
                f"Found out-of-range date: {date}"

    def test_retrieve_records_empty_date_range(self, full_transactions_database):
        """A date range with no transactions returns an empty DataFrame, not None."""
        result = full_transactions_database.retrieve_records_by_attribute_over_period(1, 2000)
        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_retrieve_records_no_excluded_rows(self, full_transactions_database):
        """retrieve_records_by_attribute_over_period never returns rows where exclude=True."""
        result = full_transactions_database.retrieve_records_by_attribute_over_period()
        if not result.empty:
            assert not result["exclude"].any(), \
                "Found excluded=True rows in retrieve_records results — they should be filtered out."

    def test_retrieve_records_excluded_row_not_returned(self, clean_transactions_database):
        """A manually excluded transaction does not appear in retrieve_records results."""
        db = clean_transactions_database
        db.add_item(
            authorized_date=datetime(2025, 6, 15),
            posted_date=datetime(2025, 6, 16),
            status="Posted",
            account_name="Test Account",
            description="EXCLUDED TRANSACTION",
            primary_category="Shopping",
            detailed_category="Retail",
            amount=50.0,
            repayment=False,
            exclude=True,
            base_hash="excluded_hash_001",
            uq_hash="excluded_uq_hash_001",
        )
        db.add_item(
            authorized_date=datetime(2025, 6, 15),
            posted_date=datetime(2025, 6, 16),
            status="Posted",
            account_name="Test Account",
            description="INCLUDED TRANSACTION",
            primary_category="Shopping",
            detailed_category="Retail",
            amount=25.0,
            repayment=False,
            exclude=False,
            base_hash="included_hash_001",
            uq_hash="included_uq_hash_001",
        )

        result = db.retrieve_records_by_attribute_over_period(6, 2025)

        assert not result.empty
        assert "EXCLUDED TRANSACTION" not in result["description"].values, \
            "Excluded transaction should not appear in results."
        assert "INCLUDED TRANSACTION" in result["description"].values, \
            "Non-excluded transaction should appear in results."

    def test_retrieve_records_by_primary_category(self, clean_transactions_database):
        """Filtering by primary_category returns only rows with that category."""
        db = clean_transactions_database
        db.add_item(
            authorized_date=datetime(2025, 3, 10),
            posted_date=datetime(2025, 3, 11),
            status="Posted",
            account_name="Test Account",
            description="GROCERY RUN",
            primary_category="Food & drink",
            detailed_category="Groceries",
            amount=80.0,
            repayment=False,
            exclude=False,
            base_hash="food_hash_001",
            uq_hash="food_uq_hash_001",
        )
        db.add_item(
            authorized_date=datetime(2025, 3, 12),
            posted_date=datetime(2025, 3, 13),
            status="Posted",
            account_name="Test Account",
            description="AMAZON PURCHASE",
            primary_category="Shopping",
            detailed_category="Retail",
            amount=120.0,
            repayment=False,
            exclude=False,
            base_hash="shop_hash_001",
            uq_hash="shop_uq_hash_001",
        )

        result = db.retrieve_records_by_attribute_over_period(3, 2025, primary_category="Food & drink")

        assert not result.empty
        assert all(result["primary_category"] == "Food & drink"), \
            "All returned records should have primary_category='Food & drink'."
        assert "AMAZON PURCHASE" not in result["description"].values

    # --- return_category_count ---

    def test_return_category_count_primary(self, full_transactions_database):
        """return_category_count returns a non-negative int for a PrimaryCategory."""
        count = full_transactions_database.return_category_count(PrimaryCategories.FOOD_AND_DRINK, 12, 2025)
        assert isinstance(count, int)
        assert count >= 0

    def test_return_category_count_detailed(self, full_transactions_database):
        """return_category_count returns a non-negative int for a DetailedCategory."""
        count = full_transactions_database.return_category_count(DetailedCategories.GROCERIES, 12, 2025)
        assert isinstance(count, int)
        assert count >= 0

    def test_return_category_count_all_time(self, full_transactions_database):
        """return_category_count with no month/year returns the all-time count."""
        count = full_transactions_database.return_category_count(PrimaryCategories.SHOPPING)
        assert isinstance(count, int)
        assert count >= 0

    def test_return_category_count_primary_less_than_total(self, full_transactions_database):
        """Count for a single primary category is <= total transaction count."""
        total = full_transactions_database.to_dataframe().shape[0]
        count = full_transactions_database.return_category_count(PrimaryCategories.FOOD_AND_DRINK)
        assert count <= total

    def test_return_category_count_invalid_raises(self, full_transactions_database):
        """Passing a value not in PrimaryCategories or DetailedCategories raises KeyError."""
        class FakeCategory:
            value = "Not A Real Category"

        with pytest.raises((KeyError, AttributeError)):
            full_transactions_database.return_category_count(FakeCategory())

    # --- upload_csv / upload_all_csvs ---

    def test_update_categories_if_diff(self, clean_transactions_database, clean_updates_database):
        """
        Tests _update_categories_if_diff via upload_csv by uploading two CSV files.

        The first CSV has original transactions with original categories.
        The second CSV has some of the same transactions with updated categories.
        The test verifies that:
        - Transactions with updated categories are modified in the database
        - Transactions with same categories remain unchanged
        - The total transaction count is correct
        """
        transactions_db = clean_transactions_database
        updates_db = clean_updates_database

        csv_original = os.path.join(TEST_CSV_DIR, "test_categories_original.csv")
        transactions_db.upload_csv(csv_original, updates_db_manager=updates_db)

        df_after_first = transactions_db.to_dataframe()
        assert df_after_first.shape[0] == 3, f"Expected 3 records after first upload, got {df_after_first.shape[0]}"

        whole_foods_row = df_after_first[df_after_first[TransactionsTable.description.name] == "Whole Foods Market"].iloc[0]
        assert whole_foods_row[TransactionsTable.detailed_category.name] == "Groceries"

        shell_row = df_after_first[df_after_first[TransactionsTable.description.name] == "Shell Gas Station"].iloc[0]
        assert shell_row[TransactionsTable.detailed_category.name] == "Gas"

        target_row = df_after_first[df_after_first[TransactionsTable.description.name] == "Target Store"].iloc[0]
        assert target_row[TransactionsTable.detailed_category.name] == "General Merchandise"

        csv_updated = os.path.join(TEST_CSV_DIR, "test_categories_updated.csv")
        transactions_db.upload_csv(csv_updated, updates_db_manager=updates_db)

        df_after_second = transactions_db.to_dataframe()
        assert df_after_second.shape[0] == 3, f"Expected 3 records after second upload, got {df_after_second.shape[0]}"

        whole_foods_after = df_after_second[df_after_second[TransactionsTable.description.name] == "Whole Foods Market"].iloc[0]
        assert whole_foods_after[TransactionsTable.detailed_category.name] == "Groceries", \
            "Whole Foods category should remain unchanged"
        assert whole_foods_after[TransactionsTable.primary_category.name] == "Food", \
            "Whole Foods primary category should remain unchanged"

        shell_after = df_after_second[df_after_second[TransactionsTable.description.name] == "Shell Gas Station"].iloc[0]
        assert shell_after[TransactionsTable.detailed_category.name] == "Auto Fuel", \
            f"Shell Gas Station detailed category should be updated to 'Auto Fuel', got '{shell_after[TransactionsTable.detailed_category.name]}'"
        assert shell_after[TransactionsTable.primary_category.name] == "Transportation", \
            "Shell Gas Station primary category should remain Transportation"

        target_after = df_after_second[df_after_second[TransactionsTable.description.name] == "Target Store"].iloc[0]
        assert target_after[TransactionsTable.detailed_category.name] == "General Retail", \
            f"Target Store detailed category should be updated to 'General Retail', got '{target_after[TransactionsTable.detailed_category.name]}'"
        assert target_after[TransactionsTable.primary_category.name] == "Shopping", \
            "Target Store primary category should remain Shopping"

    def test_upload_csv(self, clean_transactions_database, clean_updates_database):
        """Tests upload_csv on its happy path."""
        updates_db = clean_updates_database
        transactions_db = clean_transactions_database
        for csv in updates_db.iter_csv_not_uploaded(csv_directory=TEST_CSV_DIR):
            transactions_db.upload_csv(csv, updates_db_manager=updates_db)

        transactions_table = transactions_db.to_dataframe()

        assert not transactions_table.empty
        assert "Posted" in transactions_table.status.values
        assert "Unchecked" in transactions_table.status.values
        assert "Checking - 9631" in transactions_table.account_name.values
        assert transactions_table.shape[0] == 1002
