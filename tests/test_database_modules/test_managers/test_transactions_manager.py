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


# ─── helpers ──────────────────────────────────────────────────────────────────

def _make_db_transactions_record(
    date: datetime,
    description: str,
    primary_category: str,
    detailed_category: str,
    amount: float,
    exclude: bool = False,
    base_hash: str = "default_base_hash",
    uq_hash: str = "default_uq_hash",
) -> dict:
    """Returns a dict suitable for direct add_item insertion into the transactions table."""
    return {
        "authorized_date": date,
        "posted_date": date,
        "status": "Posted",
        "account_name": "Test Account",
        "description": description,
        "primary_category": primary_category,
        "detailed_category": detailed_category,
        "amount": amount,
        "repayment": False,
        "exclude": exclude,
        "base_hash": base_hash,
        "uq_hash": uq_hash,
    }


# =========================UpdatesTableManager===================================

class TestUpdatesTableManager:

    def test_generate_update_entry_raises_on_duplicate(self, clean_updates_database):
        """generate_update_entry raises DuplicateError when the same filepath is uploaded again."""
        with pytest.raises(DuplicateError):
            clean_updates_database.generate_update_entry(duplicate_update_item["filepath"], TableStatus.COMPLETE)

    def test_generate_update_entry_allows_status_change(self, clean_updates_database):
        """generate_update_entry allows the same filepath to be re-uploaded with a different status."""
        clean_updates_database.generate_update_entry(new_update_item["filepath"], TableStatus.INCOMPLETE)
        clean_updates_database.generate_update_entry(new_update_item["filepath"], TableStatus.COMPLETE)

        df = clean_updates_database.to_dataframe()
        assert df.filepath.isin([new_update_item["filepath"]]).any()
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
        """Returns a non-empty DataFrame for Dec 2025 with valid category columns and numeric values."""
        report_df = full_transactions_database.generate_monthly_category_report(12, 2025)

        assert isinstance(report_df, pd.DataFrame)
        assert not report_df.empty

        all_category_values = pd.Series(
            [m.value for m in PrimaryCategories] + [m.value for m in DetailedCategories]
        )
        assert report_df.shape == (len(all_category_values), 3)

        all_valid_columns = set(format_column_names(all_category_values))
        invalid_cats = [cat for cat in report_df.index if cat not in all_valid_columns]
        assert not invalid_cats, f"Report contains unexpected column names: {invalid_cats}"

        for col in report_df.columns:
            assert pd.api.types.is_numeric_dtype(report_df[col]), \
                f"Column '{col}' should be numeric, got {report_df[col].dtype}"

    def test_generate_monthly_category_report_empty(self, full_transactions_database):
        """generate_monthly_category_report returns an empty DataFrame with correct columns for a month with no data."""
        report_df = full_transactions_database.generate_monthly_category_report(1, 2000)

        assert isinstance(report_df, pd.DataFrame)
        assert report_df.empty

    # --- retrieve_records_by_attribute_over_period ---

    def test_retrieve_records_by_month_year(self, full_transactions_database):
        """Returns a non-empty DataFrame for Dec 2025 where all dates fall within December 2025."""
        result = full_transactions_database.retrieve_records_by_attribute_over_period(12, 2025)
        assert isinstance(result, pd.DataFrame)
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
        db.add_item(**_make_db_transactions_record(
            datetime(2025, 6, 15), "EXCLUDED TRANSACTION", "Shopping", "Retail", 50.0,
            exclude=True, base_hash="excluded_hash_001", uq_hash="excluded_uq_hash_001",
        ))
        db.add_item(**_make_db_transactions_record(
            datetime(2025, 6, 15), "INCLUDED TRANSACTION", "Shopping", "Retail", 25.0,
            exclude=False, base_hash="included_hash_001", uq_hash="included_uq_hash_001",
        ))

        result = db.retrieve_records_by_attribute_over_period(6, 2025)

        assert not result.empty
        assert "EXCLUDED TRANSACTION" not in result["description"].values, \
            "Excluded transaction should not appear in results."
        assert "INCLUDED TRANSACTION" in result["description"].values, \
            "Non-excluded transaction should appear in results."

    def test_retrieve_records_by_primary_category(self, clean_transactions_database):
        """Filtering by primary_category returns only rows with that category."""
        db = clean_transactions_database
        db.add_item(**_make_db_transactions_record(
            datetime(2025, 3, 10), "GROCERY RUN", "Food & drink", "Groceries", 80.0,
            base_hash="food_hash_001", uq_hash="food_uq_hash_001",
        ))
        db.add_item(**_make_db_transactions_record(
            datetime(2025, 3, 12), "AMAZON PURCHASE", "Shopping", "Retail", 120.0,
            base_hash="shop_hash_001", uq_hash="shop_uq_hash_001",
        ))

        result = db.retrieve_records_by_attribute_over_period(3, 2025, primary_category="Food & drink")

        assert not result.empty
        assert all(result["primary_category"] == "Food & drink"), \
            "All returned records should have primary_category='Food & drink'."
        assert "AMAZON PURCHASE" not in result["description"].values

    # --- retrieve_month_year_pairs ---

    def test_retrieve_month_year_pairs_full_db(self, full_transactions_database):
        """Checks if retrieve_month_year_pairs can accurately extract data and return in proper format"""
        pairs = full_transactions_database.retrieve_month_year_pairs()

        assert len(pairs) > 0
        assert isinstance(pairs, list)
        assert isinstance(pairs[0], tuple)
        assert len(pairs[0]) == 2
    
    def test_retrieve_month_year_pairs_empty_db(self, clean_transactions_database):
        """Checks if retrieve_month_year_pairs can accurately extract data and return in proper format"""
        pairs = clean_transactions_database.retrieve_month_year_pairs()

        assert pairs == []

    # --- return_category_count ---

    def test_return_category_count_by_type(self, full_transactions_database):
        """return_category_count returns a non-negative int for both PrimaryCategory and DetailedCategory inputs."""
        primary_count = full_transactions_database.return_category_count(PrimaryCategories.FOOD_AND_DRINK, 12, 2025)
        assert isinstance(primary_count, int)
        assert primary_count >= 0

        detailed_count = full_transactions_database.return_category_count(DetailedCategories.GROCERIES, 12, 2025)
        assert isinstance(detailed_count, int)
        assert detailed_count >= 0

    def test_return_category_count_all_time(self, full_transactions_database):
        """return_category_count with no month/year returns the all-time count, which is <= total row count."""
        total = full_transactions_database.to_dataframe().shape[0]
        count = full_transactions_database.return_category_count(PrimaryCategories.SHOPPING)
        assert isinstance(count, int)
        assert count >= 0
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
        transactions_db.upload_csv(csv_original)

        df_after_first = transactions_db.to_dataframe()
        assert df_after_first.shape[0] == 3, f"Expected 3 records after first upload, got {df_after_first.shape[0]}"

        whole_foods_row = df_after_first[df_after_first[TransactionsTable.description.name] == "Whole Foods Market"].iloc[0]
        assert whole_foods_row[TransactionsTable.detailed_category.name] == "Groceries"

        shell_row = df_after_first[df_after_first[TransactionsTable.description.name] == "Shell Gas Station"].iloc[0]
        assert shell_row[TransactionsTable.detailed_category.name] == "Gas"

        target_row = df_after_first[df_after_first[TransactionsTable.description.name] == "Target Store"].iloc[0]
        assert target_row[TransactionsTable.detailed_category.name] == "General Merchandise"

        csv_updated = os.path.join(TEST_CSV_DIR, "test_categories_updated.csv")
        transactions_db.upload_csv(csv_updated)

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
            transactions_db.upload_csv(csv)

        transactions_table = transactions_db.to_dataframe()

        assert not transactions_table.empty
        assert "Posted" in transactions_table.status.values
        assert "Unchecked" in transactions_table.status.values
        assert "Checking - 9631" in transactions_table.account_name.values
        assert transactions_table.shape[0] == 1002

    def test_upload_csv_returns_empty_list_for_new_records(self, clean_transactions_database, clean_updates_database):
        """upload_csv returns an empty list when all records in the CSV are new (no duplicates)."""
        transactions_db = clean_transactions_database
        csv_original = os.path.join(TEST_CSV_DIR, "test_categories_original.csv")
        result = transactions_db.upload_csv(csv_original)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_upload_csv_returns_updated_records(self, clean_transactions_database, clean_updates_database):
        """
        upload_csv returns only the ORM records whose categories were actually changed.

        Uploading test_categories_updated.csv over test_categories_original.csv should return
        Shell Gas Station and Target Store (2 updated), but not Whole Foods Market (unchanged).
        """
        transactions_db = clean_transactions_database

        csv_original = os.path.join(TEST_CSV_DIR, "test_categories_original.csv")
        transactions_db.upload_csv(csv_original)

        csv_updated = os.path.join(TEST_CSV_DIR, "test_categories_updated.csv")
        result = transactions_db.upload_csv(csv_updated)

        assert isinstance(result, list)
        assert len(result) == 2

        descriptions = {item.description for item in result}
        assert "Shell Gas Station" in descriptions
        assert "Target Store" in descriptions
        assert "Whole Foods Market" not in descriptions

        shell = next(item for item in result if item.description == "Shell Gas Station")
        assert shell.detailed_category == "Auto Fuel"
        assert shell.primary_category == "Transportation"

        target = next(item for item in result if item.description == "Target Store")
        assert target.detailed_category == "General Retail"
        assert target.primary_category == "Shopping"

    def test_upload_all_csvs_returns_updated_records(self, clean_transactions_database, clean_updates_database, tmp_path):
        """
        upload_all_csvs returns only the ORM records whose categories were actually changed
        across all CSVs processed.

        Seeds the DB with two original CSV files, then calls upload_all_csvs on an isolated
        directory containing both updated CSVs. Expects 4 updated records total:
        Shell Gas + Target (from file 1), Netflix + Starbucks (from file 2).
        Amazon and Whole Foods are unchanged and must not appear in the result.
        """
        import shutil
        transactions_db = clean_transactions_database

        category_fixtures = os.path.join(TEST_CSV_DIR, "category_fixtures")
        csv_original = os.path.join(TEST_CSV_DIR, "test_categories_original.csv")
        csv_original_2 = os.path.join(category_fixtures, "test_categories_original_2.csv")
        transactions_db.upload_csv(csv_original)
        transactions_db.upload_csv(csv_original_2)

        shutil.copy(os.path.join(TEST_CSV_DIR, "test_categories_updated.csv"), tmp_path)
        shutil.copy(os.path.join(category_fixtures, "test_categories_updated_2.csv"), tmp_path)

        result = transactions_db.upload_all_csvs(csv_dir=str(tmp_path))

        assert isinstance(result, list)
        assert len(result) == 4

        descriptions = {item.description for item in result}
        assert "Shell Gas Station" in descriptions
        assert "Target Store" in descriptions
        assert "Netflix" in descriptions
        assert "Starbucks" in descriptions
        assert "Whole Foods Market" not in descriptions
        assert "Amazon" not in descriptions

        shell = next(item for item in result if item.description == "Shell Gas Station")
        assert shell.detailed_category == "Auto Fuel"

        target = next(item for item in result if item.description == "Target Store")
        assert target.detailed_category == "General Retail"

        netflix = next(item for item in result if item.description == "Netflix")
        assert netflix.detailed_category == "Streaming"

        starbucks = next(item for item in result if item.description == "Starbucks")
        assert starbucks.detailed_category == "Coffee"
    

def test_generate_monthly_category_report_speed(full_transactions_database):
    """Test that generate_monthly_category_report executes within an acceptable time frame."""
    import time
    times = []
    for i in range(10):
        start_time = time.time()
        full_transactions_database.generate_monthly_category_report(12, 2025)
        end_time = time.time()
        elapsed_time = end_time - start_time
        times.append(elapsed_time)
        logger.info(f"generate_monthly_category_report executed in {elapsed_time:.6f} seconds.")
    avg_time = sum(times) / len(times)
    logger.info(f"Average execution time over 10 runs: {avg_time:.6f} seconds.")


def test_category_total_spending_repeat_speed(full_transactions_database):
    """Test that generate_monthly_category_report executes within an acceptable time frame."""
    import time
    from budgy.utils.analysis_utils import PrimaryCategories, DetailedCategories
    times = []
    for i in range(10):
        start_time = time.time()
        for member in list(PrimaryCategories) + list(DetailedCategories):
            full_transactions_database.category_total_spending(member, month=12, year=2025)

        end_time = time.time()
        elapsed_time = end_time - start_time
        times.append(elapsed_time)
        logger.info(f"category_total_spending for all categories executed in {elapsed_time:.6f} seconds.")
        avg_time = sum(times) / len(times)
    logger.info(f"Average execution time over 10 runs: {avg_time:.6f} seconds.")


def test_all_category_average_spending_speed(full_transactions_database):
    """Test that generate_monthly_category_report executes within an acceptable time frame."""
    import time
    times = []
    for i in range(10):
        start_time = time.time()
        full_transactions_database.all_category_average_spending(month=12, year=2025)
        end_time = time.time()
        elapsed_time = end_time - start_time
        times.append(elapsed_time)
        logger.info(f"all_category_average_spending for all categories executed in {elapsed_time:.6f} seconds.")
        avg_time = sum(times) / len(times)
    logger.info(f"Average execution time over 10 runs: {avg_time:.6f} seconds.")