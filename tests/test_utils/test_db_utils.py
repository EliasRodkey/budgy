#!python3
"""
budgy.utils.tests.test_utils.test_db_utils

Tests for budgy.utils.db_utils module.
"""
# Standard library imports
from datetime import datetime
from collections import defaultdict
import os
import pytest
import sys

# Third-party imports
import pandas as pd

# Local imports
from budgy.utils.db_utils import (
    DatabaseManager, DatabaseFile, DuplicateError,
    TableStatus, transactions_table_manager, update_table_manager, 
    TransactionsTable, UpdatesTable, generate_update_entry,
    generate_base_hash,
    iter_csv_not_uploaded, iter_val_csv_file, 
    upload_csv_to_db, columns
)
from local_db.utils import map_dtype_to_sql

# Initialize module logger
import logging
logger = logging.getLogger(__name__)

TEST_CSV_DIR = os.path.join(os.getcwd(), "tests", "test_utils", "test_csv_download_files")
TEST_DB_DIR = os.path.join(os.getcwd(), "tests", "test_utils", "test_database")
TEST_DB_FILENAME = "test_database.db"
TEST_DB_FILEPATH = os.path.join(TEST_DB_DIR, TEST_DB_FILENAME)

test_db_file = DatabaseFile(TEST_DB_FILEPATH, TEST_DB_DIR)
test_transaction_manager = DatabaseManager(TransactionsTable, test_db_file)
test_updates_manager = DatabaseManager(UpdatesTable, test_db_file)

update_items = [
    {
        "timestamp": datetime(2024, 1, 1),
        "filepath": os.path.join(TEST_CSV_DIR, "TEST_UPDATE.csv"),
        "status": TableStatus.COMPLETE
    },
    {
        "timestamp": datetime(2024, 1, 2),
        "filepath": os.path.join(TEST_CSV_DIR, "transactions_1.csv"),
        "status": TableStatus.COMPLETE
    },
    {
        "timestamp": datetime(2024, 1, 3),
        "filepath": os.path.join(TEST_CSV_DIR, "transactions_2.csv"),
        "status": TableStatus.INCOMPLETE
    },
    {
        "timestamp": datetime(2024, 1, 5),
        "filepath": os.path.join(TEST_CSV_DIR, "hsbifunsdovns.csv"),
        "status": "Error - hdchiboenc"
    }
]

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


@pytest.fixture()
def clean_updates_database():
    """Fixture to clean the database before and after each test"""
    db_manager = test_updates_manager

    try:
        # Setup: Clean the database
        db_manager.add_multiple_items(update_items)
        yield db_manager  # Provide the db_manager to the test

    except Exception:
        db_manager.session.rollback()  # Rollback the session if an exception occurs
        raise

    finally:
        db_manager.clear_table()

        # Teardown: Ensure the session is closed
        db_manager.end_session()

@pytest.fixture()
def clean_transactions_database():
    """Fixture to clean the database before and after each test"""
    db_manager = test_transaction_manager

    try:
        yield db_manager  # Provide the db_manager to the test

    except Exception:
        db_manager.session.rollback()  # Rollback the session if an exception occurs
        raise

    finally:
        db_manager.clear_table()

        # Teardown: Ensure the session is closed
        db_manager.end_session()


def test_db_file_creation():
    """Test that the database files are created successfully."""
    logger.debug("Starting test...")
    db_file = transactions_table_manager.file
    db_file.create()
    assert os.path.exists(db_file.file_path), "Database file does not exist."


def test_transactions_table_creation():
    """Test that the Transactions table is created successfully and data could be retrieved from it."""
    logger.debug("Starting test...")
    transactions_table_manager.add_item(**record_1)
    items = transactions_table_manager.fetch_all_items()
    logger.debug(f"Fetched items from transaction_updates table:\n{items}")
    assert items is not None, "Failed to fetch items from Transactions table."
    assert isinstance(items, list), "Fetched items is not a list."

    as_df = transactions_table_manager.to_dataframe()
    logger.info(f"Transactions table as dataframe:\n{as_df}")
    assert not as_df.empty, "Dataframe conversion resulted in empty dataframe."
    assert list(as_df.columns) == (['id'] + list(record_1.keys()) + ["uq_hash"]), "Dataframe columns do not match expected columns."

    transactions_table_manager.delete_items_by_attribute(**{"description": "TEST TRANSACTION"})


def test_updates_table_creation():
    """Test that the transaction_updates table is created successfully and data could be retrieved from it."""
    logger.debug("Starting test...")
    update_table_manager.add_item(**duplicate_update_item)
    items = update_table_manager.fetch_all_items()
    logger.debug(f"Fetched items from transaction_updates table:\n{items}")
    assert items is not None, "Failed to fetch items from transaction_updates table."
    assert items is not None, "Failed to fetch items from Transactions table."
    assert isinstance(items, list), "Fetched items is not a dataframe."

    as_df = update_table_manager.to_dataframe()
    logger.info(f"Updates table as dataframe:\n{as_df}")
    assert not as_df.empty, "Dataframe conversion resulted in empty dataframe."
    assert list(as_df.columns) == ['id'] + list(duplicate_update_item.keys()), "Dataframe columns do not match expected columns."

    update_table_manager.delete_items_by_attribute(**{"filepath": "TEST_UPDATE.csv"})


# ==================NOTE: This is where the basic schema tests end and the more sophisticated csv upload test cases begin.============== #


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
    assert transactions_table.shape[0] == 999