#!python3
"""
budgy.utils.tests.test_db_utils.py

Tests for budgy.utils.db_utils module.
"""
# Standard library imports
import datetime
import os
import pytest
import sys

# Import logging utilities
import logging
from loggers import configure_logger, LoggingHandlerController
from budgy.utils.file_utils import EDirectories

# Local imports
from budgy.utils.db_utils import transactions_table_manager, updates_table_manager
from local_db.utils import map_dtype_to_sql

# Iniitialize logger
logger = logging.getLogger(__name__)
log_handlers: LoggingHandlerController = configure_logger(logger, log_direcotry=EDirectories.LOG_DIR)


def test_db_file_creation():
    """Test that the database files are created successfully."""
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
    """Test that the Transactions table is created successfully."""
    transactions_table_manager.add_item(**new_item)
    items = transactions_table_manager.fetch_all_items()
    logger.debug(f"Fetched items from transaction_updates table: {items}")
    assert items is not None, "Failed to fetch items from Transactions table."
    assert type(items) == list, "Fetched items is not a list."

    as_df = transactions_table_manager.to_dataframe()
    logger.info(f"Transactions table as dataframe:\n{as_df}")
    assert not as_df.empty, "Dataframe conversion resulted in empty dataframe."
    assert list(as_df.columns) == ['id'] + list(new_item.keys()), "Dataframe columns do not match expected columns."


update_item = {
        "datetime": datetime.datetime(2024, 1, 1),
        "filename": "TEST_UPDATE.csv",
        "status": "completed"
    }

def test_updates_table_creation():
    """Test that the transaction_updates table is created successfully."""
    updates_table_manager.add_item(**update_item)
    items = updates_table_manager.fetch_all_items()
    logger.debug(f"Fetched items from transaction_updates table: {items}")
    assert items is not None, "Failed to fetch items from transaction_updates table."
    assert items is not None, "Failed to fetch items from Transactions table."
    assert type(items) == list, "Fetched items is not a list."

    as_df = transactions_table_manager.to_dataframe()
    assert not as_df.empty, "Dataframe conversion resulted in empty dataframe."
    assert list(as_df.columns) == ['id'] + list(new_item.keys()), "Dataframe columns do not match expected columns."


def test_clear_tables():
    """Test clearing all items from both tables."""
    pass