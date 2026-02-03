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
from budgy.intake.csv import iter_csv_uploaded, iter_csv_file, columns
from budgy.utils.db_utils import updates_table_manager

# Initialize module logger
import logging
logger = logging.getLogger(__name__)

TEST_CSV_DIR = os.path.join(os.getcwd(), "tests", "test_intake", "test_csv_download_files")
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
        for item in update_items:
            db_manager.delete_items_by_attribute(filename=item["filename"])

        # Teardown: Ensure the session is closed
        db_manager.end_session()


def test_iter_csv_uploaded(clean_database):
    """Tests the iter csv uploaded function to make sure it can correctly identify which file still needs uploading"""
    db_manager = clean_database
    uploaded_files = db_manager.to_dataframe()["filename"]
    for csv in iter_csv_uploaded(csv_filepath=TEST_CSV_DIR):
        assert csv not in uploaded_files


def test_iter_csv():
    for csv in iter_csv_uploaded(csv_filepath=TEST_CSV_DIR):
        for record in iter_csv_file(csv):
            for col in columns:
                assert col.dest in record
            if record["amount"] > 0:
                assert record["status"] == "Unchecked"
            if col.dest == "authorized_date" or col.dest == "posted_date":
                assert isinstance(record[col.dest], datetime)

# TODO: Write a test for the db upload, including edge cases. and error handling!