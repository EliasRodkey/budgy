#!python3
"""
budgy.utils.tests.test_utils.test_db_utils

Tests for budgy.utils.db_utils module.
"""
# Standard library imports
from datetime import datetime
import os
import pytest
import sys

# Third-party imports
import pandas as pd

# Local imports
from budgy.utils.db_utils import (
    DatabaseManager, DatabaseFile,
    TableStatus, transactions_table_manager, updates_table_manager, 
    TransactionsTable, UpdatesTable, generate_update_entry,
    DuplicateError, iter_csv_not_uploaded, iter_csv_file, 
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
        "status": "completed"
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

new_transaction_item = {
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
    transactions_table_manager.add_item(**new_transaction_item)
    items = transactions_table_manager.fetch_all_items()
    logger.debug(f"Fetched items from transaction_updates table:\n{items}")
    assert items is not None, "Failed to fetch items from Transactions table."
    assert isinstance(items, list), "Fetched items is not a list."

    as_df = transactions_table_manager.to_dataframe()
    logger.info(f"Transactions table as dataframe:\n{as_df}")
    assert not as_df.empty, "Dataframe conversion resulted in empty dataframe."
    assert list(as_df.columns) == ['id'] + list(new_transaction_item.keys()), "Dataframe columns do not match expected columns."

    transactions_table_manager.delete_items_by_attribute(**{"description": "TEST TRANSACTION"})


def test_updates_table_creation():
    """Test that the transaction_updates table is created successfully and data could be retrieved from it."""
    logger.debug("Starting test...")
    updates_table_manager.add_item(**duplicate_update_item)
    items = updates_table_manager.fetch_all_items()
    logger.debug(f"Fetched items from transaction_updates table:\n{items}")
    assert items is not None, "Failed to fetch items from transaction_updates table."
    assert items is not None, "Failed to fetch items from Transactions table."
    assert isinstance(items, list), "Fetched items is not a dataframe."

    as_df = updates_table_manager.to_dataframe()
    logger.info(f"Updates table as dataframe:\n{as_df}")
    assert not as_df.empty, "Dataframe conversion resulted in empty dataframe."
    assert list(as_df.columns) == ['id'] + list(duplicate_update_item.keys()), "Dataframe columns do not match expected columns."

    updates_table_manager.delete_items_by_attribute(**{"filepath": "TEST_UPDATE.csv"})


# ==================NOTE: This is where the basic schema tests end and the more sophisticated csv upload test cases begin.============== #


def test_generate_update_entry(clean_updates_database):
    """Tests the updates_table_manager to make sure that we are not creating multiple uploads for the same file"""
    try:
        generate_update_entry(duplicate_update_item["filepath"], TableStatus.COMPLETE, update_table_manager=clean_updates_database)

    except Exception as e:
        assert isinstance(e, DuplicateError)
    
    finally:
        # This should execute without an error since the status is changing
        generate_update_entry(new_update_item["filepath"], TableStatus.INCOMPLETE, update_table_manager=clean_updates_database)
        generate_update_entry(new_update_item["filepath"], TableStatus.COMPLETE, update_table_manager=clean_updates_database)

        df = clean_updates_database.to_dataframe()
        clean_updates_database.clear_table()

    assert df.filepath.isin([duplicate_update_item["filepath"]]).any()

    new_update_idx = df.index[df.filepath == new_update_item["filepath"]]

    status = df.iloc[new_update_idx, :].status.iloc[0]
    assert status == TableStatus.COMPLETE


def test_iter_csv__not_uploaded(clean_updates_database):
    """Tests the iter csv uploaded function to make sure it can correctly identify which file still needs uploading"""
    db_manager = clean_updates_database
    uploaded_files = db_manager.to_dataframe()["filename"]
    for csv in iter_csv_not_uploaded(csv_directory=TEST_CSV_DIR, update_table_manager=db_manager):
        assert csv not in uploaded_files
        assert csv not in [item["filename"] for item in update_items]


def test_iter_csv(clean_updates_database):
    for csv_filepath in iter_csv_not_uploaded(csv_directory=TEST_CSV_DIR, update_table_manager=clean_updates_database):
        for record in iter_csv_file(csv_filepath, columns):
            for col in columns:
                assert col.dest in record
            if record["amount"] > 0:
                assert record["status"] == "Unchecked"
            if col.dest == "authorized_date" or col.dest == "posted_date":
                assert isinstance(record[col.dest], datetime)


# TODO: This should only test CSV ripping and data validation! may want to think about wrapping all of this under db_utils or a new pipeline module!
def test_iter_csv(clean_updates_database):
    for csv_filepath in iter_csv_not_uploaded(csv_directory=TEST_CSV_DIR, update_table_manager=clean_updates_database):
        for record in iter_csv_file(csv_filepath, columns):
            for col in columns:
                assert col.dest in record
            if record["amount"] > 0:
                assert record["status"] == "Unchecked"
            if col.dest == "authorized_date" or col.dest == "posted_date":
                assert isinstance(record[col.dest], datetime)


def test_upload_csv_to_db(clean_transactions_database, clean_updates_database):
    """Tests the upload_csv_to_db function on it's happy path."""
    updates_db = clean_updates_database
    transactions_db = clean_transactions_database
    for csv in iter_csv_not_uploaded(csv_directory=TEST_CSV_DIR, update_table_manager=updates_db):
        upload_csv_to_db(csv, record_db_manager=transactions_db)
    
    transactions_table = transactions_db.to_dataframe()

    transactions_table.head()
    assert not transactions_table.empty
    assert "Posted" in transactions_table.status
    assert "Unchecked" in transactions_table.status
    assert "Checking - 9631" in transactions_table.account_name
    assert transactions_table.shape[0] == 999