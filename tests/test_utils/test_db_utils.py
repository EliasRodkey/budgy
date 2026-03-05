#!python3
"""
budgy.utils.tests.test_utils.test_db_utils

Tests for budgy.utils.db_utils module — CSV processing and database upload functions.
"""
# Standard library imports
from datetime import datetime
import os

# Local imports
from local_db import DuplicateError
from budgy.utils.db_models import TransactionsTable, TableStatus
from budgy.utils.db_utils import (
    generate_update_entry, generate_base_hash,
    iter_csv_not_uploaded, iter_val_csv_file,
    update_categories_if_diff, upload_csv_to_db, columns
)
from tests.test_utils.conftest import TEST_CSV_DIR

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

record_1 = {
    "authorized_date": datetime(2024, 1, 1),
    "posted_date": datetime(2024, 1, 2),
    "status": "pending",
    "account_name": "Checking Account",
    "description": "TEST TRANSACTION",
    "primary_category": "Food",
    "detailed_category": "Groceries",
    "amount": 150.75,
    "repayment": False,
    "exclude": False
}

record_2 = {
    "authorized_date": datetime(2026, 2, 5),
    "posted_date": datetime(2026, 2, 8),
    "account_name": "Bilt Rewards Credit Card",
    "description": "TEST TRANSACTION 2",
    "primary_category": "Food",
    "detailed_category": "Dining and Drinks",
    "amount": 68.79,
}

duplicate_record_1 = {
    "authorized_date": datetime(2025, 9, 16),
    "posted_date": datetime(2025, 9, 20),
    "account_name": "American Express Credit Card",
    "description": "TEST TRANSACTION DUPLICATE",
    "primary_category": "Travel",
    "detailed_category": "Hotels",
    "amount": 475.99,
}

duplicate_record_2 = {
    "authorized_date": datetime(2025, 9, 16),
    "posted_date": datetime(2025, 9, 20),
    "account_name": "American Express Credit Card",
    "description": "TEST TRANSACTION DUPLICATE",
    "primary_category": "Travel",
    "detailed_category": "Hotels",
    "amount": 475.99,
}


# ==================NOTE: CSV upload function tests.============== #


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
            from tests.test_utils.conftest import update_items
            assert csv not in [item["filepath"] for item in update_items]


def test_generate_base_hash():
    """Tests the generate_base_hash function to make sure that it is generating the same hash for the same record and different hashes for different records"""

    hash_1 = generate_base_hash(record_1)
    hash_2 = generate_base_hash(record_2)
    hash_3 = generate_base_hash(duplicate_record_1)
    hash_4 = generate_base_hash(duplicate_record_2)

    assert hash_1 != hash_2, f"Hashes for different records should not match: {hash_1} == {hash_2}"
    assert hash_1 != hash_3, f"Hashes for different records should not match: {hash_1} == {hash_3}"
    assert hash_3 == hash_4, f"Hashes for identical records do not match: {hash_1} != {hash_2}"


def test_iter_csv(clean_updates_database):
    """Tests the iter_csv_file function to make sure that it is correctly parsing the csv file and yielding the correct records with the correct types"""
    for csv_filepath in iter_csv_not_uploaded(csv_directory=TEST_CSV_DIR, updates_db_manager=clean_updates_database):
        for record in iter_val_csv_file(csv_filepath, columns):
            for col in columns:
                assert col.dest in record
            if record["amount"] > 0:
                assert record["status"] == "Unchecked"
            if col.dest == "authorized_date" or col.dest == "posted_date":
                assert isinstance(record[col.dest], datetime)


def test_iter_csv_hash(clean_updates_database):
    """Tests iter_csv_file function to make sure the hashes created are all unique"""
    for csv_filepath in iter_csv_not_uploaded(csv_directory=TEST_CSV_DIR, updates_db_manager=clean_updates_database):
        hashes = set()
        for record in iter_val_csv_file(csv_filepath, columns):
            assert record["uq_hash"] is not None, "Hash value is missing from record."
            assert record["uq_hash"] not in hashes, f"Duplicate hash value found: {record['uq_hash']}"
            hashes.add(record["uq_hash"])
        assert len(hashes) == len(list(iter_val_csv_file(csv_filepath, columns))), f"Expected 999 unique hashes, but found {len(hashes)}."


def test_update_categories_if_diff(clean_transactions_database, clean_updates_database):
    """
    Tests the update_categories_if_diff function by uploading two CSV files.

    The first CSV has original transactions with original categories.
    The second CSV has some of the same transactions with updated categories.
    The test verifies that:
    - Transactions with updated categories are modified in the database
    - Transactions with same categories remain unchanged
    - The total transaction count is correct
    """
    transactions_db = clean_transactions_database
    updates_db = clean_updates_database

    # Upload the first CSV file with original categories
    csv_original = os.path.join(TEST_CSV_DIR, "test_categories_original.csv")
    upload_csv_to_db(csv_original, transactions_db_manager=transactions_db, updates_db_manager=updates_db)

    # Fetch the transactions after first upload
    df_after_first = transactions_db.to_dataframe()

    # Verify initial data is in the database
    assert df_after_first.shape[0] == 3, f"Expected 3 records after first upload, got {df_after_first.shape[0]}"

    # Store original detailed categories for verification
    original_categories = {}
    for _, row in df_after_first.iterrows():
        key = (row[TransactionsTable.description.name], row[TransactionsTable.amount.name])
        original_categories[key] = {
            "primary": row[TransactionsTable.primary_category.name],
            "detailed": row[TransactionsTable.detailed_category.name]
        }

    # Verify first transaction has original category (unchanged in second upload)
    whole_foods_row = df_after_first[df_after_first[TransactionsTable.description.name] == "Whole Foods Market"].iloc[0]
    assert whole_foods_row[TransactionsTable.detailed_category.name] == "Groceries"

    # Verify second transaction has original category (will be updated)
    shell_row = df_after_first[df_after_first[TransactionsTable.description.name] == "Shell Gas Station"].iloc[0]
    assert shell_row[TransactionsTable.detailed_category.name] == "Gas"

    # Verify third transaction has original category (will be updated)
    target_row = df_after_first[df_after_first[TransactionsTable.description.name] == "Target Store"].iloc[0]
    assert target_row[TransactionsTable.detailed_category.name] == "General Merchandise"

    # Upload the second CSV file with updated categories
    csv_updated = os.path.join(TEST_CSV_DIR, "test_categories_updated.csv")
    upload_csv_to_db(csv_updated, transactions_db_manager=transactions_db, updates_db_manager=updates_db)

    # Fetch the transactions after second upload
    df_after_second = transactions_db.to_dataframe()

    # Verify we still have 3 records (no duplicates were added)
    assert df_after_second.shape[0] == 3, f"Expected 3 records after second upload, got {df_after_second.shape[0]}"

    # Verify UNCHANGED transaction (Whole Foods with "Groceries")
    # This should NOT be modified since categories are identical
    whole_foods_after = df_after_second[df_after_second[TransactionsTable.description.name] == "Whole Foods Market"].iloc[0]
    assert whole_foods_after[TransactionsTable.detailed_category.name] == "Groceries", \
        "Whole Foods category should remain unchanged"
    assert whole_foods_after[TransactionsTable.primary_category.name] == "Food", \
        "Whole Foods primary category should remain unchanged"

    # Verify UPDATED transaction 1 (Shell Gas Station)
    # Updated from "Gas" to "Auto Fuel"
    shell_after = df_after_second[df_after_second[TransactionsTable.description.name] == "Shell Gas Station"].iloc[0]
    assert shell_after[TransactionsTable.detailed_category.name] == "Auto Fuel", \
        f"Shell Gas Station detailed category should be updated to 'Auto Fuel', got '{shell_after[TransactionsTable.detailed_category.name]}'"
    assert shell_after[TransactionsTable.primary_category.name] == "Transportation", \
        "Shell Gas Station primary category should remain Transportation"

    # Verify UPDATED transaction 2 (Target Store)
    # Updated from "General Merchandise" to "General Retail"
    target_after = df_after_second[df_after_second[TransactionsTable.description.name] == "Target Store"].iloc[0]
    assert target_after[TransactionsTable.detailed_category.name] == "General Retail", \
        f"Target Store detailed category should be updated to 'General Retail', got '{target_after[TransactionsTable.detailed_category.name]}'"
    assert target_after[TransactionsTable.primary_category.name] == "Shopping", \
        "Target Store primary category should remain Shopping"


def test_upload_csv_to_db(clean_transactions_database, clean_updates_database):
    """Tests the upload_csv_to_db function on it's happy path."""
    updates_db = clean_updates_database
    transactions_db = clean_transactions_database
    for csv in iter_csv_not_uploaded(csv_directory=TEST_CSV_DIR, updates_db_manager=updates_db):
        upload_csv_to_db(csv, transactions_db_manager=transactions_db, updates_db_manager=updates_db)

    transactions_table = transactions_db.to_dataframe()

    assert not transactions_table.empty
    assert "Posted" in transactions_table.status.values
    assert "Unchecked" in transactions_table.status.values
    assert "Checking - 9631" in transactions_table.account_name.values
    assert transactions_table.shape[0] == 1002
