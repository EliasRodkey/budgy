#!python3
"""
budgy.database_modules.models.transactions.py -
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
from local_db import BaseTable, ESQLDataTypes

# Local imports
from .common import Column, parse_date

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


# first arg comes from CSF input col names, consider changing to Enum
transaction_columns = [
    Column("Authorized Date", TransactionsTable.authorized_date.name, parse_date),
    Column("Posted Date", TransactionsTable.posted_date.name, parse_date),
    Column("Status", TransactionsTable.status.name, str),
    Column("Account Name", TransactionsTable.account_name.name, str),
    Column("Description", TransactionsTable.description.name, str),
    Column("Primary Category", TransactionsTable.primary_category.name, str),
    Column("Detailed Category", TransactionsTable.detailed_category.name, str),
    Column("Amount", TransactionsTable.amount.name, float),
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

    id = ESQLDataTypes.Column(ESQLDataTypes.Integer, primary_key=True, autoincrement=True)
    timestamp = ESQLDataTypes.Column(ESQLDataTypes.DateTime)
    filepath = ESQLDataTypes.Column(ESQLDataTypes.String, unique=True)
    status = ESQLDataTypes.Column(ESQLDataTypes.String)
