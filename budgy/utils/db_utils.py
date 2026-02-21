"""
budgy.utils.db_utils.py

Contains funcitons for general database opteration. 
Creates database tables and files.
"""
# Standard library imports
import csv
from collections import namedtuple
from datetime import datetime
from enum import Enum
import os
from typing import Dict, Generator, List

# Import database management classes and enums from local_db module
from local_db import DatabaseFile, BaseTable, DatabaseManager, ESQLDataTypes, DuplicateError

# Local imports
from budgy.utils.file_utils import EDirectories, LoggingExtras, get_csv_filenames

# initialize module logger
import logging
logger = logging.getLogger(__name__)



class TransactionsTable(BaseTable):
    """
    Class representing the Transactions table in the database.
    This table stores all the transaction data imported from CSV files.
    
    Database Structure:
    table name: transactions
    Columns:
        - id: Integer, Primary Key, Auto Increment (unique identifier for each transaction)
        - authorized_date: DateTime
        - posted_date: DateTime
        - status: String
        - account_name: String
        - description: String
        - primary_category: String
        - detailed_category: String
        - amount: Float
        - repayment: Boolean
        - exclude: Boolean
    """

    __tablename__ = "transactions"

    id = ESQLDataTypes.Column(ESQLDataTypes.Integer, primary_key=True, autoincrement=True)
    authorized_date =  ESQLDataTypes.Column(ESQLDataTypes.DateTime)
    posted_date = ESQLDataTypes.Column(ESQLDataTypes.DateTime)
    status = ESQLDataTypes.Column(ESQLDataTypes.String)
    account_name = ESQLDataTypes.Column(ESQLDataTypes.String)
    description = ESQLDataTypes.Column(ESQLDataTypes.String)
    primary_category = ESQLDataTypes.Column(ESQLDataTypes.String)
    detailed_category = ESQLDataTypes.Column(ESQLDataTypes.String)
    amount = ESQLDataTypes.Column(ESQLDataTypes.Float)
    repayment = ESQLDataTypes.Column(ESQLDataTypes.Boolean)
    exclude = ESQLDataTypes.Column(ESQLDataTypes.Boolean)



class UpdatesTable(BaseTable):
    """
    Class representing the transaction_updates table in the database.
    This table stores metadata about CSV file imports and their statuses.
    
    Database Structure:
    table name: transactions
    Columns:
        - id: Integer, Primary Key, Auto Increment (unique identifier for each update record)
        - timestamp: DateTime
        - filepath: String
        - status: String
    """

    __tablename__ = "transaction_updates"

    id = ESQLDataTypes.Column(ESQLDataTypes.Integer, primary_key=True, autoincrement=True)
    timestamp = ESQLDataTypes.Column(ESQLDataTypes.DateTime)
    filepath = ESQLDataTypes.Column(ESQLDataTypes.String, unique=True)
    status = ESQLDataTypes.Column(ESQLDataTypes.String)


    
class TableStatus(str, Enum):
    """Enum class with different possible status' for the database records"""
    POSTED = "Posted"
    UNCHECKED = "Unchecked"
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"

    def __str__(self):
        return str(self.value)



transactions_table_manager = DatabaseManager(TransactionsTable, DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR))
updates_table_manager = DatabaseManager(UpdatesTable, DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR))



Column = namedtuple('Column', 'src dest convert')



def parse_timestamp(text) -> datetime:
    return datetime.strptime(text, "%Y-%m-%d")


columns = [
    Column("Authorized Date", TransactionsTable.authorized_date.name, parse_timestamp),
    Column("Posted Date", TransactionsTable.posted_date.name, parse_timestamp),
    Column("Status", TransactionsTable.status.name, str),
    Column("Account Name", TransactionsTable.account_name.name, str),
    Column("Description", TransactionsTable.description.name, str),
    Column("Primary Category", TransactionsTable.primary_category.name, str),
    Column("Detailed Category", TransactionsTable.detailed_category.name, str),
    Column("Amount", TransactionsTable.amount.name, float),
]


#=======================NOTE: End of db / schema setup code, Start of db specific funcitons.==================================#

# NOTE: We should be checking the updates BEFORE we actually want to generate a new entry! make check for filepath function.

def generate_update_entry(filepath: str, status: TableStatus, update_table_manager: DatabaseManager=updates_table_manager):
    """
    Creates an update entry for the update table and handles potential errors.
    
    Args:
        filepath (str): the filepath being uploaded to the transactions database
        status (UpdatesTableStatus): The status to register the update with
        update_table_manager (DatabaseManager): The table that the update is being pushed to (changed for testing)
    """
    matching_items = update_table_manager.fetch_items_by_attribute(filepath=filepath)

    if matching_items:
        if matching_items[0].status == TableStatus.COMPLETE:
            logger.error(f"File {filepath} already exists in {update_table_manager.table_name}", extra={LoggingExtras.FILE: filepath})
            raise DuplicateError(filepath, UpdatesTable, message="Entry for filepath already exists in:")
        
        else:
            update_table_manager.update_item(matching_items[0].id, status=status)
    
    else:
        update_table_manager.add_item(
            timestamp=datetime.now(),
            filepath=filepath,
            status=status
        )


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


def validate_transaction(csv_record: Dict, columns: List[Column]):
    """Validates each record against the Schema to ensure that the data is correctly uploaded to the database."""
    db_record = {}
    for col in columns:
        value = csv_record[col.src]
        db_record[col.dest] = col.convert(value)
            
    return set_status_unchecked(db_record)


# Check whether or not the CSV data file has been uploaded to the database and return filename
def iter_csv_not_uploaded(csv_directory=EDirectories.CSV_DIR, update_table_manager: DatabaseManager=updates_table_manager) -> Generator:
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
        elif item[0].status == TableStatus.COMPLETE:
            logger.info(f"CSV file {os.path.basename(filepath)} has already been uploaded to the database.", extra={LoggingExtras.FILE: filepath})
        
        # If the returned item's status is not set to complete, then field the filepath
        elif item[0].status != TableStatus.COMPLETE:
            logger.info(f"CSV file {os.path.basename(filepath)} has not yet been uploaded to the database.", extra={LoggingExtras.FILE: filepath})
            yield filepath
        
        # Raise an error for unhandled case
        else:
            logger.error()


# Iterate through the lines in the CSV and validate each line
def iter_csv_file(csv_filepath: str, columns: List[Column]) -> Generator:
    """Iterates through each line in the CSV file and provides them as a generator."""
    logger.info(f"Iterating and validating CSV file: {os.path.basename(csv_filepath)}", extra={LoggingExtras.FILE: csv_filepath})

    with open(csv_filepath, mode="r", encoding="utf-8") as f:
        transactions = csv.DictReader(f)

        for csv_record in transactions:
            db_record = validate_transaction(csv_record, columns)
            yield db_record


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


def clear_tables(force: bool=False):
    logger.warning(f"Database table clearing initiated. force: {force}")
    if not force:
        answer = input("Are you sure you would like to clear the database tables? (Y/n)")
        if answer == "Y":
            logger.info(f"Database table clearing accepted. Clearing database tables.")
            transactions_table_manager.clear_table()
            updates_table_manager.clear_table()

        elif answer == "n":
            logger.info(f"Database table clearing rejected. Aborting.")
    
    else:
        transactions_table_manager.clear_table()
        updates_table_manager.clear_table()
