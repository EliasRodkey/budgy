#!python3
"""
budgy.utils.tests.test_intake.test_csv

Tests for budgy.intake.csv module.
"""
# Standard library imports
import datetime
import os
import pytest
import sys

# Third-party imports
import pandas as pd

# Local imports
from budgy.utils.db_utils import updates_table_manager
from local_db.utils import map_dtype_to_sql

# Initialize module logger
import logging
logger = logging.getLogger(__name__)


update_items = [
    {
        "datetime": datetime.datetime(2024, 1, 1),
        "filename": "TEST_UPDATE.csv",
        "status": "completed"
    },
    {
        "datetime": datetime.datetime(2024, 1, 2),
        "filename": "transactions_1.csv",
        "status": "completed"
    },
    {
        "datetime": datetime.datetime(2024, 1, 3),
        "filename": "transactions_2.csv",
        "status": "completed"
    },
    {
        "datetime": datetime.datetime(2024, 1, 5),
        "filename": "hsbifunsdovns.csv",
        "status": "Error - hdchiboenc"
    }
]
@pytest.fixture(autouse=True)
def clean_database():
    """Fixture to clean the database before and after each test"""
    db_manager = updates_table_manager

    try:
        # Setup: Clean the database
        db_manager.add_multiple_items(update_items)
        yield db_manager  # Provide the db_manager to the test

    except Exception:
        db_manager.session.rollback()  # Rollback the session if an exception occurs
        raise

    finally:
        # Teardown: Ensure the session is closed
        db_manager.end_session()
        

update_items = {
        "datetime": datetime.datetime(2024, 1, 1),
        "filename": "TEST_UPDATE.csv",
        "status": "completed"
    }