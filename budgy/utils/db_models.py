#!python3
"""
Contains ORM table definitions, database managers, and CSV column mappings for budgy.

Module Overview:
===============
Classes:
--------
    - TransactionsTable: ORM class representing the transactions table in the database.
    - UpdatesTable: ORM class representing the transaction_updates table in the database.
    - TableStatus: Enum class defining possible status values for database records.

Module-Level Variables:
-----------------------
    - transactions_table_manager: DatabaseManager instance for the TransactionsTable.
        Manages all database operations on the transactions table.
    - update_table_manager: DatabaseManager instance for the UpdatesTable.
        Manages all database operations on the updates table.
    - Column: Named tuple defining CSV-to-database column mappings (src, dest, convert).
    - columns: List of Column namedtuples mapping CSV headers to TransactionsTable columns
        with type conversion functions for transaction data import.

Dependencies:
- local_db: Custom ORM module providing DatabaseFile, BaseTable, DatabaseManager,
    ESQLDataTypes, DuplicateError, and UniqueConstraint classes.
- budgy.utils.file_utils: Provides EDirectories enum for standard directory paths.
    budgy.utils.db_models.py
"""
# Standard library imports
from collections import namedtuple
from datetime import datetime
from enum import Enum

# Import database management classes and enums from local_db module
from local_db import DatabaseFile, BaseTable, DatabaseManager, ESQLDataTypes, DuplicateError
from local_db.base_table import UniqueConstraint

# Local imports
from budgy.utils.file_utils import EDirectories

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
        - base_hash: a hash value generated based on the transaction information, tells us if 2 transactions have the same information.
        - uq_hash: a unique hash value generated based on the transaction information and number of occurances to ensure that we can detect duplicates
                  without relying on the position of the transaction in the csv file.
                  This is important because some csv files have multiple transactions with the same information such as
                  split venmo transactions or multiple purchases from a bar on the same day.
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
    base_hash = ESQLDataTypes.Column(ESQLDataTypes.String)
    uq_hash = ESQLDataTypes.Column(ESQLDataTypes.String, unique=True)



class UpdatesTable(BaseTable):
    """
    Class representing the transaction_updates table in the database.
    This table stores metadata about CSV file imports and their statuses.

    Database Structure:
    table name: transaction_updates
    Columns:
        - id: Integer, Primary Key, Auto Increment (unique identifier for each update record)
        - timestamp: DateTime
        - filepath: String (unique constraint — prevents re-uploading the same CSV)
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
    COMPLETE = "Complete"
    INCOMPLETE = "Incomplete"

    def __str__(self):
        return str(self.value)



transactions_table_manager = DatabaseManager(TransactionsTable, DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR))
update_table_manager = DatabaseManager(UpdatesTable, DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR))



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
