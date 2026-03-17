#!python3
"""
tests.test_database_modules.test_managers.test_transactions_manager.py

Tests for budgy.database_modules.managers.transactions_manager.py module — Database query and update functions fro Transactions and Updates
"""
# Standard library imports
from datetime import datetime
import os

# Third party imports
import pandas as pd

# Local imports
from budgy.database_modules.models.common import TableStatus
from budgy.database_modules.managers.transaction_manager import DuplicateError, generate_update_entry, iter_csv_not_uploaded, generate_monthly_category_report
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


def test_generate_update_entry(clean_updates_database):
    """Tests the updates_table_manager to make sure that we are not creating multiple uploads for the same file"""
    try:
        generate_update_entry(duplicate_update_item["filepath"], TableStatus.COMPLETE, updates_db_manager=clean_updates_database)

    except Exception as e:
        assert isinstance(e, DuplicateError)

    finally:
        # This should execute without an error since the status is changing
        generate_update_entry(new_update_item["filepath"], TableStatus.INCOMPLETE, updates_db_manager=clean_updates_database)
        generate_update_entry(new_update_item["filepath"], TableStatus.COMPLETE, updates_db_manager=clean_updates_database)

        df = clean_updates_database.to_dataframe()
        clean_updates_database.clear_table()

    assert df.filepath.isin([duplicate_update_item["filepath"]]).any()

    new_update_idx = df.index[df.filepath == new_update_item["filepath"]]

    status = df.iloc[new_update_idx, :].status.iloc[0]
    assert status == TableStatus.COMPLETE


def test_iter_csv__not_uploaded(clean_updates_database):
    """Tests the iter csv uploaded function to make sure it can correctly identify which file still needs uploading"""
    db_manager = clean_updates_database
    uploaded_files = db_manager.to_dataframe()["filepath"]
    for csv in iter_csv_not_uploaded(csv_directory=TEST_CSV_DIR, updates_db_manager=db_manager):
        db_item = db_manager.fetch_items_by_attribute(filepath=csv)

        # If an ORM object is returned, check to make sure that the status is set to incomplete.
        if db_item:
            assert db_item[0].status != TableStatus.COMPLETE

        # Otherwise the filepath should not appear in the retrieved db values
        else:
            assert csv not in uploaded_files
            from tests.conftest import update_items
            assert csv not in [item["filepath"] for item in update_items]


def test_generate_monthly_category_report(full_transactions_database):
    """Test the generate_monthly_category_report function for a specific month and year."""
    month = 12
    year = 2025

    report_df = generate_monthly_category_report(month, year, full_transactions_database)

    # Check that the report is a DataFrame and has the expected columns
    assert isinstance(report_df, pd.DataFrame), "Report should be a pandas DataFrame."
    expected_columns = [member.name.lower().replace(" ", "_") for member in PrimaryCategories] + \
                       [member.name.lower().replace(" ", "_") for member in DetailedCategories] + \
                       ["total_amount"]
    assert all(col in report_df.columns for col in expected_columns), f"Report should contain the expected columns: {expected_columns}"