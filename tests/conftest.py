#!python3
"""
Shared pytest fixtures and test database setup for test_utils.

Provides:
    - Test database path constants (TEST_CSV_DIR, TEST_DB_DIR, etc.)
    - Test DatabaseManager instances (test_transaction_manager, test_updates_manager)
    - clean_updates_database fixture: populates the updates table with sample data, tears down after each test
    - clean_transactions_database fixture: yields an empty transactions table, tears down after each test
    - full_transactions_database fixture: populates the transactions table with data from a test CSV, tears down after each test
"""
import os
from datetime import datetime

import pytest
from local_db import DatabaseFile, DatabaseManager
from loggers import configure_logging

from budgy.utils.db_models import TransactionsTable, UpdatesTable, TableStatus
from budgy.utils.file_utils import EDirectories
from budgy.utils.db_utils import upload_csv_to_db


@pytest.fixture(scope="session", autouse=True)
def configure_test_logging():
    configure_logging(log_directory=EDirectories.LOG_DIR)


TEST_CSV_DIR = os.path.join(os.getcwd(), "tests", "test_utils", "test_csv_download_files")
TEST_DB_DIR = os.path.join(os.getcwd(), "tests", "test_utils", "test_database")
TEST_DB_FILENAME = "test_database.db"
TEST_DB_FILEPATH = os.path.join(TEST_DB_DIR, TEST_DB_FILENAME)

test_db_file = DatabaseFile(TEST_DB_FILEPATH, TEST_DB_DIR)
test_transaction_manager = DatabaseManager(TransactionsTable, test_db_file)
test_updates_manager = DatabaseManager(UpdatesTable, test_db_file)

TEST_FULL_TRANSACTIONS_CSV = os.path.join(TEST_CSV_DIR, "SoFi-Relay-All-Transactions_2025-12-31.csv")

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


@pytest.fixture()
def clean_updates_database():
    """Fixture to populate and clean the updates table before and after each test."""
    db_manager = test_updates_manager

    try:
        db_manager.add_multiple_items(update_items)
        yield db_manager

    except Exception:
        db_manager.session.rollback()
        raise

    finally:
        db_manager.clear_table()
        db_manager.end_session()


@pytest.fixture()
def clean_transactions_database():
    """Fixture to provide and clean the transactions table before and after each test."""
    db_manager = test_transaction_manager

    try:
        yield db_manager

    except Exception:
        db_manager.session.rollback()
        raise

    finally:
        db_manager.clear_table()
        db_manager.end_session()


@pytest.fixture()
def full_transactions_database():
    """Fixture to provide and loaded transactions table before and after each test."""
    db_manager = test_transaction_manager

    # Add transactions from the loaded csv to the test db
    upload_csv_to_db(
        TEST_FULL_TRANSACTIONS_CSV, 
        transactions_db_manager=db_manager, 
        updates_db_manager=test_updates_manager
    )

    try:
        yield db_manager

    except Exception:
        db_manager.session.rollback()
        raise

    finally:
        db_manager.clear_table()
        db_manager.end_session()