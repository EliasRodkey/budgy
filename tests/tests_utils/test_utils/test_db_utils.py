#!python3
"""
budgy.utils.tests.test_utils.test_db_utils

Tests for budgy.utils.db_utils module.
"""
# Standard library imports
import datetime
import os
import pytest
import sys

# Third-party imports
import pandas as pd

# Local imports
from budgy.utils.db_utils import transactions_table_manager, updates_table_manager
from local_db.utils import map_dtype_to_sql

# Initialize module logger
import logging
logger = logging.getLogger(__name__)


def test_db_file_creation():
    """Test that the database files are created successfully."""
    logger.debug("Starting test...")
    db_file = transactions_table_manager.file
    db_file.create()
    assert os.path.exists(db_file.file_path), "Database file does not exist."


new_item = {
    "authorized_date": datetime.datetime(2024, 1, 1),
    "posted_date": datetime.datetime(2024, 1, 2),
    "status": "pending",
    "account_name": "Checking Account",
    "description": "TEST TRANSACTION",
    "primary_category": "Food",
    "detailed_category": "Groceries",
    "amount": 150.75,
    "repayment": False,
    "exclude": False
}
def test_transactions_table_creation():
    """Test that the Transactions table is created successfully and data could be retrieved from it."""
    logger.debug("Starting test...")
    transactions_table_manager.add_item(**new_item)
    items = transactions_table_manager.fetch_all_items()
    logger.debug(f"Fetched items from transaction_updates table:\n{items}")
    assert items is not None, "Failed to fetch items from Transactions table."
    assert isinstance(items, list), "Fetched items is not a dataframe."

    as_df = transactions_table_manager.to_dataframe()
    logger.info(f"Transactions table as dataframe:\n{as_df}")
    assert not as_df.empty, "Dataframe conversion resulted in empty dataframe."
    assert list(as_df.columns) == ['id'] + list(new_item.keys()), "Dataframe columns do not match expected columns."

    transactions_table_manager.delete_items_by_attribute(**{"description": "TEST TRANSACTION"})


update_item = {
        "datetime": datetime.datetime(2024, 1, 1),
        "filename": "TEST_UPDATE.csv",
        "status": "completed"
    }
def test_updates_table_creation():
    """Test that the transaction_updates table is created successfully and data could be retrieved from it."""
    logger.debug("Starting test...")
    updates_table_manager.add_item(**update_item)
    items = updates_table_manager.fetch_all_items()
    logger.debug(f"Fetched items from transaction_updates table:\n{items}")
    assert items is not None, "Failed to fetch items from transaction_updates table."
    assert items is not None, "Failed to fetch items from Transactions table."
    assert isinstance(items, list), "Fetched items is not a dataframe."

    as_df = updates_table_manager.to_dataframe()
    logger.info(f"Updates table as dataframe:\n{as_df}")
    assert not as_df.empty, "Dataframe conversion resulted in empty dataframe."
    assert list(as_df.columns) == ['id'] + list(update_item.keys()), "Dataframe columns do not match expected columns."

    updates_table_manager.delete_items_by_attribute(**{"filename": "TEST_UPDATE.csv"})