"""
budgy.utils.db_utils.py

Contains funcitons for general database opteration. 
Creates database tables and files.
"""
# Standard library imports
from datetime import datetime
from enum import Enum
import os

# Import database management classes and enums from local_db module
from local_db import DatabaseFile, BaseTable, DatabaseManager, ESQLDataTypes, DuplicateError

# Local imports
from budgy.utils.file_utils import EDirectories, LoggingExtras

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



class TransactionTableStatus(str, Enum):
    """Enum class with different possible status' for transaction records"""
    POSTED = "Posted"
    UNCHECKED = "Unchecked"

    def __str__(self):
        return str(self.value)



class UpdatesTable(BaseTable):
    """
    Class representing the transaction_updates table in the database.
    This table stores metadata about CSV file imports and their statuses.
    
    Database Structure:
    table name: transactions
    Columns:
        - id: Integer, Primary Key, Auto Increment (unique identifier for each update record)
        - timestamp: DateTime
        - filename: String
        - status: String
    """

    __tablename__ = "transaction_updates"

    id = ESQLDataTypes.Column(ESQLDataTypes.Integer, primary_key=True, autoincrement=True)
    timestamp = ESQLDataTypes.Column(ESQLDataTypes.DateTime)
    filepath = ESQLDataTypes.Column(ESQLDataTypes.String, unique=True)
    status = ESQLDataTypes.Column(ESQLDataTypes.String)



class UpdatesTableStatus(str, Enum):
    """Enum class with different possible status' for transaction records"""
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"

    def __str__(self):
        return str(self.value)



transactions_table_manager = DatabaseManager(TransactionsTable, DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR))
updates_table_manager = DatabaseManager(UpdatesTable, DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR))


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


def generate_update_entry(filepath: str, status: UpdatesTableStatus, update_table_manager: DatabaseManager=updates_table_manager):
    """
    Creates an update entry for the update table and handles potential errors.
    
    Args:
        filepath (str): the filepath being uploaded to the transactions database
        status (UpdatesTableStatus): The status to register the update with
        update_table_manager (DatabaseManager): The table that the update is being pushed to (changed for testing)
    """
    matching_items = update_table_manager.fetch_items_by_attribute(filepath=filepath)

    if matching_items:
        if matching_items[0].status == UpdatesTableStatus.COMPLETE:
            logger.error(f"File {filepath} already exists in {update_table_manager.table_name}", extra={LoggingExtras.FILE: filepath})
            raise DuplicateError(filepath, UpdatesTable, message="Entry for filepath already exists in:")
        
        else:
            update_table_manager.update_item(matching_items[0].id, status=status)
    
    else:
        updates_table_manager.add_item(
            timestamp=datetime.now(),
            filepath=filepath,
            status=status
        )