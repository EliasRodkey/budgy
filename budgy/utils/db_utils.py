"""
budgy.utils.db_utils.py

Contains funcitons for general database opteration. 
Creates database tables and files.
"""

# Import logging utilities
import logging
from loggers import configure_logger
from .file_utils import EDirectories

# Import database management classes and enums from local_db module
from local_db import DatabaseFile, BaseTable, DatabaseManager, ESQLDataTypes

# Iniitialize logger
logger = logging.getLogger(__name__)
configure_logger(logger, EDirectories.LOG_DIR)



class TransactionsTable(BaseTable):
    """Class representing the Transactions table in the database."""

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
    """Class representing the transaction_updates table in the database."""

    __tablename__ = "transaction_updates"

    id = ESQLDataTypes.Column(ESQLDataTypes.Integer, primary_key=True, autoincrement=True)
    datetime = ESQLDataTypes.Column(ESQLDataTypes.DateTime)
    filename = ESQLDataTypes.Column(ESQLDataTypes.String)
    status = ESQLDataTypes.Column(ESQLDataTypes.String)



transactions_table_manager = DatabaseManager(TransactionsTable, DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR))
updates_table_manager = DatabaseManager(UpdatesTable, DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR))