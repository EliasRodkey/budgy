#! python3
"""
budgy.intake.csv
Reads data from raw SoFi CSV exports. Validates and exports data to local transactions database. 

Classes:
    - 

Functions:
    - 
"""

# Standard library imports
from collections import namedtuple
import csv
from datetime import datetime
import os
from typing import Dict, Generator, List

# Custom package imports
from local_db import DatabaseManager

# Local application imports
from ..utils.db_utils import TransactionTableStatus, UpdatesTable, UpdatesTableStatus, DuplicateError, transactions_table_manager, updates_table_manager
from ..utils.file_utils import EDirectories, LoggingExtras, get_csv_filenames

# Initialize module logger
import logging
logger = logging.getLogger(__name__)


# Check whether or not the CSV data file has been uploaded to the database and return filename
def iter_csv_uploaded(csv_directory=EDirectories.CSV_DIR, update_table_manager: DatabaseManager=updates_table_manager) -> Generator:
    """Iterates through the CSV files in the csv_downlaods directory and checks whether or not they have been uploaded to the database."""

    # Iterate over CSV files in directory
    for filepath in get_csv_filenames(csv_directory=csv_directory):
        item = update_table_manager.fetch_items_by_attribute(filename=filepath)

        # If no item is returned, yield the file path.
        if not item:
            logger.info(f"CSV file {os.path.basename(filepath)} has not yet been uploaded to the database.", extra={LoggingExtras.FILE: filepath})
            yield filepath

        # If more than one value is returned, an error occured somewhere
        elif len(item) >= 2:
            filename = item[0].filename
            logger.error(f"Multiple items found with the same filename, {filename}", extra={LoggingExtras.FILE: filename})
            raise DuplicateError(filename, UpdatesTable)
        
        # If the returned item has it's status set to complete, do nothing
        elif item[0].status == UpdatesTableStatus.COMPLETE:
            logger.info(f"CSV file {os.path.basename(filepath)} has already been uploaded to the database.", extra={LoggingExtras.FILE: filepath})
        
        # If the returned item's status is not set to complete, then field the filepath
        elif item[0].status != UpdatesTableStatus.COMPLETE:
            logger.info(f"CSV file {os.path.basename(filepath)} has not yet been uploaded to the database.", extra={LoggingExtras.FILE: filepath})
            yield filepath
        
        # Raise an error for unhandled case
        else:
            logger.error()


# ============ NOTE: Below here is the only actual CSV pulling and validation code!, the rest should be related to the DB, pull / check / push ==================== #
# Define database structure and schema
Column = namedtuple('Column', 'src dest convert')

def parse_timestamp(text) -> datetime:
    return datetime.strptime(text, "%Y-%m-%d")

transaction_db_col_names = transactions_table_manager.table_class.get_column_names()

columns = [
    Column("Authorized Date", transaction_db_col_names[1], parse_timestamp),
    Column("Posted Date", transaction_db_col_names[2], parse_timestamp),
    Column("Status", transaction_db_col_names[3], str),
    Column("Account Name", transaction_db_col_names[4], str),
    Column("Description", transaction_db_col_names[5], str),
    Column("Primary Category", transaction_db_col_names[6], str),
    Column("Detailed Category", transaction_db_col_names[7], str),
    Column("Amount", transaction_db_col_names[8], float),
]

def set_status_unchecked(record: dict) -> dict:
    """If the amount of the transaction is greater than zero (i.e. transfer or income), we may want to check and see if it is a repayment or needs to be excluded"""
    if record[transaction_db_col_names[8]] > 0:
        record[transaction_db_col_names[3]] = TransactionTableStatus.UNCHECKED
    return record


def validate_transaction(csv_record: Dict, columns: List[Column]):
    """Validates each record against the Schema to ensure that the data is correctly uploaded to the database."""
    db_record = {}
    for col in columns:
        value = csv_record[col.src]
        db_record[col.dest] = col.convert(value)
            
    return set_status_unchecked(db_record)


# Iterate through the lines in the CSV and validate each line
def iter_csv_file(csv_filepath: str, columns: List[Column]) -> Generator:
    """Iterates through each line in the CSV file and provides them as a generator."""
    logger.info(f"Iterating and validating CSV file: {os.path.basename(csv_filepath)}", extra={LoggingExtras.FILE: csv_filepath})

    with open(csv_filepath, mode="r", encoding="utf-8") as f:
        transactions = csv.DictReader(f)

        for csv_record in transactions:
            db_record = validate_transaction(csv_record, columns)
            yield db_record

# ============================================================================================== #

# Insert data into database, checking to make sure it is not a duplicate
def upload_csv_to_db(csv_filepath: str, columns: List[Column]=columns, record_db_manager: DatabaseManager=transactions_table_manager) -> bool:
    """
    Initiates the search for new CSV files, 
    converts and validates the new transactions line by line then uploads to the transactions database.
    Returns whether or not the file was uploaded successfully.
    Also enforces that no csv can be uploaded if it already has a posted upload with completed status.
    """
    for record in iter_csv_file(csv_filepath, columns):
        try:
            record_db_manager.add_item(**record)
        except Exception as e:
            logger.exception(f"Exception encountered during data upload to {record_db_manager}")
            return False
    return True
