#!python3
"""
backend.csv_modules.transactions_csv_loader
Contains functions for parsing and validating CSV transaction data.

Functions:
    - iter_val_csv_file(): Generator function that iterates through CSV file records, validates
        each against the schema, and generates unique hashes based on transaction content and
        occurrence count to detect duplicates.
    - validate_transaction(): Validates a single CSV record against the schema, performs type
        conversions on each column, and sets the status based on transaction amount.
    - generate_base_hash(): Generates a hash based on transaction content (authorized date, posted date,
        account name, description, and amount) to identify transactions with identical information.
    - set_status_unchecked(): Sets transaction status to UNCHECKED if the amount is greater than zero,
        indicating it may need manual review for repayment or exclusion classification.
"""
# Standard library imports
import csv
from collections import defaultdict
import hashlib
import os
from typing import Dict, Generator, List

# Local imports
from backend.database_modules.models.common import Field, TableStatus
from backend.database_modules.models.transactions import TransactionsTable
from backend.utils.file_utils import LoggingExtras

# initialize module logger
from pleasant_loggers import get_logger
logger = get_logger(__name__)


#============== Data validation funcitons ====================

def set_status_unchecked(record: dict) -> dict:
    """
    If the amount of the transaction is greater than zero (i.e. transfer or income),
    we may want to check and see if it is a repayment or needs to be excluded

    Args:
        record (dict): the record to check
    """
    if record[TransactionsTable.amount.name] > 0:
        record[TransactionsTable.status.name] = TableStatus.UNCHECKED
    return record


def validate_transaction(csv_record: Dict, columns: List[Field]):
    """Validates each record against the Schema to ensure that the data is correctly uploaded to the database."""
    db_record = {}
    for col in columns:
        value = csv_record[col.src].strip()
        db_record[col.dest] = col.convert(value)

    # Initialize repayment and exclude status to false for all transactions, we can update these later if needed
    db_record[TransactionsTable.repayment.name] = False
    db_record[TransactionsTable.exclude.name] = False

    return set_status_unchecked(db_record)


def generate_base_hash(record: dict) -> str:
    """
    Hash based purely on transaction content — no position.
    Uses authorized and posted date, account name, description, and amount to generate the hash.
    NOTE: Do not use primary or detailed category as those are subject to change in future!
    """
    unique_string = f"\
        {record[TransactionsTable.authorized_date.name]}:\
        {record[TransactionsTable.posted_date.name]}:\
        {record[TransactionsTable.account_name.name]}:\
        {record[TransactionsTable.description.name]}:\
        {record[TransactionsTable.amount.name]}"
    return hashlib.sha256(unique_string.encode()).hexdigest()


# Iterate through the lines in the CSV and validate each line
def iter_val_csv_file(csv_filepath: str, columns: List[Field]) -> Generator:
    """
    Iterates through each line in the CSV file and provides them as a generator.
    Also validates each line against the schema and generates a unique hash based on the record information and number of occurances

    Args:
        csv_filepath (str): the filepath of the csv being uploaded
        columns (List[Column]): the column mapping and conversion information for the csv upload
    """
    logger.info(f"Iterating and validating CSV file: {os.path.basename(csv_filepath)}", extra={LoggingExtras.FILE: csv_filepath})

    # First pass: count total occurrences of each base hash
    occurrence_counter = defaultdict(int)

    with open(csv_filepath, mode="r", encoding="utf-8") as f:
        transactions = csv.DictReader(f)

        for csv_record in transactions:
            db_record = validate_transaction(csv_record, columns)

            # Generate a unique hash for each transaction record based on the info and occurance count
            base_hash = generate_base_hash(db_record)
            count = occurrence_counter[base_hash]  # 0-indexed: first occurrence = 0
            final_hash = hashlib.sha256(f"{base_hash}:{count}".encode()).hexdigest()
            occurrence_counter[base_hash] += 1
            db_record["base_hash"] = base_hash
            db_record["uq_hash"] = final_hash

            yield db_record
