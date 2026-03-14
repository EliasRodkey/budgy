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
from local_db import DuplicateError

# Local imports
from budgy.database_modules.managers.transaction_manager import transactions_table_manager, update_table_manager
from budgy.database_modules.models.common import TableStatus

import logging
logger = logging.getLogger(__name__)


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

duplicate_update_item = {
    "timestamp": datetime(2024, 1, 1),
    "filepath": os.path.join(os.getcwd(), "tests", "test_csv_download_files", "TEST_UPDATE.csv"),
    "status": TableStatus.COMPLETE
}


def test_db_file_creation():
    """Test that the database file is created successfully."""
    logger.debug("Starting test...")
    db_file = transactions_table_manager.file
    db_file.create()
    assert os.path.exists(db_file.file_path), "Database file does not exist."


def test_transactions_table_creation():
    """Test that the TransactionsTable is created successfully and data can be retrieved from it."""
    logger.debug("Starting test...")
    transactions_table_manager.add_item(**record_1)
    items = transactions_table_manager.fetch_all_items()
    logger.debug(f"Fetched items from transactions table:\n{items}")
    assert items is not None, "Failed to fetch items from Transactions table."
    assert isinstance(items, list), "Fetched items is not a list."

    as_df = transactions_table_manager.to_dataframe()
    logger.info(f"Transactions table as dataframe:\n{as_df}")
    assert not as_df.empty, "Dataframe conversion resulted in empty dataframe."
    assert list(as_df.columns) == (['id'] + list(record_1.keys()) + ["base_hash", "uq_hash"]), "Dataframe columns do not match expected columns."

    transactions_table_manager.delete_items_by_attribute(**{"description": "TEST TRANSACTION"})


def test_updates_table_creation():
    """Test that the UpdatesTable is created successfully and data can be retrieved from it."""
    logger.debug("Starting test...")

    try:
        update_table_manager.add_item(**duplicate_update_item)
    except Exception as e:
        assert isinstance(e, DuplicateError)

    items = update_table_manager.fetch_all_items()
    logger.debug(f"Fetched items from transaction_updates table:\n{items}")
    assert items is not None, "Failed to fetch items from transaction_updates table."
    assert isinstance(items, list), "Fetched items is not a list."

    as_df = update_table_manager.to_dataframe()
    logger.info(f"Updates table as dataframe:\n{as_df}")
    assert not as_df.empty, "Dataframe conversion resulted in empty dataframe."
    assert list(as_df.columns) == ['id'] + list(duplicate_update_item.keys()), "Dataframe columns do not match expected columns."

    update_table_manager.delete_items_by_attribute(**{"filepath": "TEST_UPDATE.csv"})
