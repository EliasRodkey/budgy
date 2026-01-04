"""
budgy.utils.db_utils.py

Contains funcitons for general database opteration. 
Creates database tables and files.
"""

# Iniitialize logger
from budgy import ELF, Logger
from .file_utils import EDirectories

_logger = Logger("db_utils", EDirectories.LOG_DIR)
_logger.add_file_handler(ELF.FORMAT_LOGGER_NAME)

# Import database management classes and enums from local_db module
from local_db import ESQLDataTypes, DatabaseFile, BaseTable, DatabaseManager
Column = ESQLDataTypes.Column



class TransactionsTable(BaseTable):
    """Class representing the Transactions table in the database."""

    __table_name__ = "transactions"



class UpdatesTable(BaseTable):
    """Class representing the transaction_updates table in the database."""

    __table_name__ = "transaction_updates"