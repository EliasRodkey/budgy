#!python3
"""
backend.database_modules.models.transactions.py -
Contains ORM table definitions, database managers, and CSV column mappings for budgy.

Classes:
    - TransactionsTable: ORM class representing the transactions table in the database.
    - UpdatesTable: ORM class representing the transaction_updates table in the database.
    - TableStatus: Enum class defining possible status values for database records.

Variables:
    - columns: List of Column namedtuples mapping CSV headers to TransactionsTable columns
        with type conversion functions for transaction data import.
"""
# Custom imports
from sqlalchemy import Column, Integer, DateTime, String, Float, Boolean
from pleasant_database import BaseTable

# Local imports
from .common import Field, parse_date

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
        - notes: String (max 300 chars, edit modal only)
        - tags: String (max 10 tags, each max 30 chars, no spaces
        - base_hash: a hash value generated based on the transaction information, tells us if 2 transactions have the same information.
        - uq_hash: a unique hash value generated based on the transaction information and number of occurances to ensure that we can detect duplicates
                  without relying on the position of the transaction in the csv file.
                  This is important because some csv files have multiple transactions with the same information such as
                  split venmo transactions or multiple purchases from a bar on the same day.
    """

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    authorized_date = Column(DateTime)
    posted_date = Column(DateTime)
    status = Column(String)
    account_name = Column(String)
    description = Column(String)
    primary_category = Column(String)
    detailed_category = Column(String)
    amount = Column(Float)
    repayment = Column(Boolean)
    exclude = Column(Boolean)
    notes = Column(String) # max 300 chars, edit modal only
    tags = Column(String) # max 10 tags, each max 30 chars, no spaces
    base_hash = Column(String)
    uq_hash = Column(String, unique=True)


# first arg comes from CSF input col names, consider changing to Enum
transaction_columns = [
    Field("Authorized Date", TransactionsTable.authorized_date.name, parse_date),
    Field("Posted Date", TransactionsTable.posted_date.name, parse_date),
    Field("Status", TransactionsTable.status.name, str),
    Field("Account Name", TransactionsTable.account_name.name, str),
    Field("Description", TransactionsTable.description.name, str),
    Field("Primary Category", TransactionsTable.primary_category.name, str),
    Field("Detailed Category", TransactionsTable.detailed_category.name, str),
    Field("Amount", TransactionsTable.amount.name, float),
]



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

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime)
    filepath = Column(String, unique=True)
    status = Column(String)
