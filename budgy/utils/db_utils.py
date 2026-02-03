"""
budgy.utils.db_utils.py

Contains funcitons for general database opteration. 
Creates database tables and files.
"""
# Standard library imports
from enum import Enum

# Import database management classes and enums from local_db module
from local_db import DatabaseFile, BaseTable, DatabaseManager, ESQLDataTypes

# Local imports
from budgy.utils.file_utils import EDirectories

# Initialize module logger
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
    filename = ESQLDataTypes.Column(ESQLDataTypes.String)
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