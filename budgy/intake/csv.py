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
from typing import Dict, Generator

# Local application imports
from ..utils.db_utils import TransactionTableStatus, UpdatesTableStatus, transactions_table_manager, updates_table_manager
from ..utils.file_utils import EDirectories, LoggingExtras, get_csv_filenames

# Initialize module logger
import logging
logger = logging.getLogger(__name__)


# Check whether or not the CSV data file has been uploaded to the database and return filename
def iter_csv_uploaded(csv_filepath=EDirectories.CSV_DIR) -> Generator:
    """Iterates through the CSV files in the csv_downlaods directory and checks whether or not they have been uploaded to the database."""

    # Iterate over CSV files in directory
    for filename in get_csv_filenames(csv_filepath=csv_filepath):
        item = updates_table_manager.fetch_items_by_attribute(filename=filename)

        # If there is no result or the status is listed as complete, do not return the filename
        if item != [] or item.status == UpdatesTableStatus.COMPLETE :
            logger.info(f"CSV file {os.path.basename(filename)} has already been uploaded to the database.", extra={LoggingExtras.FILE: filename})
        else:
            logger.info(f"CSV file {os.path.basename(filename)} has not yet been uploaded to the database.", extra={LoggingExtras.FILE: filename})
            yield filename


# Define database structure and schema
Column = namedtuple('Column', 'src dest convert')

def parse_timestamp(text) -> datetime:
    return datetime.strptime(text, "%Y-%m-%d")

transaction_db_col_names = transactions_table_manager.table_class.get_column_names()

columns = [
    Column("Authorized Date", transaction_db_col_names[0], parse_timestamp),
    Column("Posted Date", transaction_db_col_names[1], parse_timestamp),
    Column("Status", transaction_db_col_names[2], str),
    Column("Account Name", transaction_db_col_names[3], str),
    Column("Description", transaction_db_col_names[4], str),
    Column("Primary Category", transaction_db_col_names[5], str),
    Column("Detailed Category", transaction_db_col_names[6], str),
    Column("Amount", transaction_db_col_names[7], float),
]

def set_status_unchecked(record: dict) -> dict:
    """If the amount of the transaction is greater than zero (i.e. transfer or income), we may want to check and see if it is a repayment or needs to be excluded"""
    if record[transaction_db_col_names[7]] > 0:
        record[transaction_db_col_names[2]] = TransactionTableStatus.UNCHECKED
    return record


def validate_transaction(csv_record: Dict):
    """Validates each record against the Schema to ensure that the data is correctly uploaded to the database."""
    db_record = {}
    for col in columns:
        value = csv_record[col.src]
        db_record[col.dest] = col.convert(value)
        
        if col.dest == transaction_db_col_names[6]:
            set_status_unchecked(db_record)
            
    return db_record


# Iterate through the lines in the CSV and validate each line
def iter_csv_file(csv_filename: str) -> Generator:
    """Iterates through each line in the CSV file and provides them as a generator."""
    logger.info(f"Iterating and validating CSV file: {os.path.basename(csv_filename)}", extra={LoggingExtras.FILE: csv_filename})

    with open(csv_filename, mode="r", encoding="utf-8") as f:
        transactions = csv.DictReader(f)

        for csv_record in transactions:
            db_record = validate_transaction(csv_record)
            yield db_record
        

# Insert data into database, checking to make sure it is not a duplicate
def upload_csv_to_db():
    """
    Initiates the search for new CSV files, 
    converts and validates the new transactions line by line then uploads to the transactions database.
    """
    for filepath in iter_csv_uploaded():
        for record in iter_csv_file(filepath):
            try:
                transactions_table_manager.add_item(**record)
            except Exception as e:
                
                # TODO: See what kinds of exceptions crop up when we have duplicates and handle smoothly.
                updates_table_manager.add_item(
                    timestamp=datetime.now(), 
                    filename=os.path.basename(filepath), 
                    status=UpdatesTableStatus.INCOMPLETE
                )

        
        updates_table_manager.add_item(
            timestamp=datetime.now(), 
            filename=os.path.basename(filepath), 
            status=UpdatesTableStatus.COMPLETE
        )
        



