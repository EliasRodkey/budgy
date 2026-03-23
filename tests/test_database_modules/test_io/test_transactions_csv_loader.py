#!python3
"""
tests.test_database_modules.test_io.test_transactions_csv_loader.py

Tests for budgy.database_modules.io.transactions_csv_loader.py module — CSV processing and database upload functions.
"""
# Standard library imports
from datetime import datetime
import os

# Local imports
from budgy.database_modules.io.transactions_csv_loader import generate_base_hash, iter_val_csv_file
from budgy.database_modules.models.transactions import transaction_columns
from tests.conftest import TEST_CSV_DIR

# Initialize module logger
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
    for csv_filepath in clean_updates_database.iter_csv_not_uploaded(csv_directory=TEST_CSV_DIR):
        for record in iter_val_csv_file(csv_filepath, transaction_columns):
            for col in transaction_columns:
                assert col.dest in record
            if record["amount"] > 0:
                assert record["status"] == "Unchecked"
            if col.dest == "authorized_date" or col.dest == "posted_date":
                assert isinstance(record[col.dest], datetime)


def test_iter_csv_hash(clean_updates_database):
    """Tests iter_csv_file function to make sure the hashes created are all unique"""
    for csv_filepath in clean_updates_database.iter_csv_not_uploaded(csv_directory=TEST_CSV_DIR):
        hashes = set()
        for record in iter_val_csv_file(csv_filepath, transaction_columns):
            assert record["uq_hash"] is not None, "Hash value is missing from record."
            assert record["uq_hash"] not in hashes, f"Duplicate hash value found: {record['uq_hash']}"
            hashes.add(record["uq_hash"])
        assert len(hashes) == len(list(iter_val_csv_file(csv_filepath, transaction_columns))), f"Expected 999 unique hashes, but found {len(hashes)}."


