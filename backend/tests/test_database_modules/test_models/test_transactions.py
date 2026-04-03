#!python3
"""
tests.test_database_modules.test_models.test_transactions

Tests for budgy.database_modules.models.transactions module — ORM table definitions and database managers.
"""
# Standard library imports
import os
from datetime import datetime

# Third party imports
import pytest
from pleasant_database import DatabaseIntegrityError

# Local imports
from backend.database_modules.models.common import TableStatus
from backend.tests.conftest import TEST_CSV_DIR, TEST_DB_FILEPATH

import logging
logger = logging.getLogger(__name__)


def _make_db_transactions_record(uq_hash: str = "test_uq_hash_001") -> dict:
    """Returns a dict suitable for direct add_item insertion into the transactions table."""
    return {
        "authorized_date": datetime(2024, 1, 1),
        "posted_date": datetime(2024, 1, 2),
        "status": "pending",
        "account_name": "Checking Account",
        "description": "TEST TRANSACTION",
        "primary_category": "Food",
        "detailed_category": "Groceries",
        "amount": 150.75,
        "repayment": False,
        "exclude": False,
        "base_hash": "test_base_hash_001",
        "uq_hash": uq_hash,
    }


def test_db_file_creation():
    """Test that the database file is created successfully."""
    assert os.path.exists(TEST_DB_FILEPATH), "Database file does not exist."


def test_transactions_table_creation(clean_transactions_database):
    """TransactionsTable supports add, fetch, and DataFrame conversion."""
    db = clean_transactions_database
    record = _make_db_transactions_record()
    db.add_item(**record)

    items = db.fetch_all_items()
    assert items is not None, "Failed to fetch items from Transactions table."
    assert isinstance(items, list), "Fetched items is not a list."

    as_df = db.to_dataframe()
    assert not as_df.empty, "Dataframe conversion resulted in empty dataframe."
    expected_cols = ["id"] + list(record.keys())
    assert list(as_df.columns) == expected_cols, "Dataframe columns do not match expected columns."


def test_updates_table_creation(clean_updates_database):
    """UpdatesTable supports fetch and DataFrame conversion; duplicate filepath raises DatabaseIntegrityError."""
    db = clean_updates_database

    duplicate_filepath = os.path.join(TEST_CSV_DIR, "TEST_UPDATE.csv")
    with pytest.raises(DatabaseIntegrityError):
        db.add_item(
            timestamp=datetime(2024, 1, 1),
            filepath=duplicate_filepath,
            status=TableStatus.COMPLETE,
        )

    items = db.fetch_all_items()
    assert items is not None, "Failed to fetch items from transaction_updates table."
    assert isinstance(items, list), "Fetched items is not a list."

    as_df = db.to_dataframe()
    assert not as_df.empty, "Dataframe conversion resulted in empty dataframe."
    assert list(as_df.columns) == ["id", "timestamp", "filepath", "status"], \
        "Dataframe columns do not match expected columns."
