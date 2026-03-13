#!python3
"""


Funcitons:
    - generate_update_entry

Variables:
    - transactions_table_manager: DatabaseManager instance for the TransactionsTable.
        Manages all database operations on the transactions table.
    - update_table_manager: DatabaseManager instance for the UpdatesTable.
        Manages all database operations on the updates table.
"""
# Standard library imports
from datetime import datetime
from typing import Generator
import os

# Custom imports
from local_db import DatabaseFile, DatabaseManager, DuplicateError

# Local imports
from budgy.database_modules.models.common import TableStatus
from budgy.database_modules.models.transactions import TransactionsTable, UpdatesTable
from budgy.utils.file_utils import EDirectories, LoggingExtras, get_csv_filenames

# initialize module logger
import logging
logger = logging.getLogger(__name__)

# Table managers
DB_FILE = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_FILEPATH)
transactions_table_manager = DatabaseManager(TransactionsTable, DB_FILE)
update_table_manager = DatabaseManager(UpdatesTable, DB_FILE)


# NOTE: We should be checking the updates BEFORE we actually want to generate a new entry! make check for filepath function.

def generate_update_entry(filepath: str, status: TableStatus, updates_db_manager: DatabaseManager=update_table_manager):
    """
    Creates an update entry for the update table and handles potential errors.

    Args:
        filepath (str): the filepath being uploaded to the transactions database
        status (UpdatesTableStatus): The status to register the update with
        update_table_manager (DatabaseManager): The table that the update is being pushed to (changed for testing)
    """
    matching_items = updates_db_manager.fetch_items_by_attribute(filepath=filepath)

    if matching_items:
        if matching_items[0].status == TableStatus.COMPLETE:
            logger.error(f"File {filepath} already exists in {updates_db_manager.table_name}", extra={LoggingExtras.FILE: filepath})
            raise DuplicateError(filepath, UpdatesTable, message="Entry for filepath already exists in:")

        else:
            updates_db_manager.update_item(matching_items[0].id, status=status)

    else:
        updates_db_manager.add_item(
            timestamp=datetime.now(),
            filepath=filepath,
            status=status
        )


# Check whether or not the CSV data file has been uploaded to the database and return filename
def iter_csv_not_uploaded(csv_directory=EDirectories.CSV_DIR, updates_db_manager: DatabaseManager=update_table_manager) -> Generator:
    """Iterates through the CSV files in the csv_downlaods directory and checks whether or not they have been uploaded to the database."""

    # Iterate over CSV files in directory
    for filepath in get_csv_filenames(csv_directory=csv_directory):
        item = updates_db_manager.fetch_items_by_attribute(filepath=filepath)

        # If no item is returned, yield the file path.
        if not item:
            logger.info(f"CSV file {os.path.basename(filepath)} has not yet been uploaded to the database.", extra={LoggingExtras.FILE: filepath})
            yield filepath

        # If more than one value is returned, an error occured somewhere
        elif len(item) >= 2:
            filepath = item[0].filepath
            logger.error(f"Multiple items found with the same filepath, {filepath}", extra={LoggingExtras.FILE: filepath})
            raise DuplicateError(filepath, UpdatesTable)

        # If the returned item has it's status set to complete, do nothing
        elif item[0].status == TableStatus.COMPLETE:
            logger.info(f"CSV file {os.path.basename(filepath)} has already been uploaded to the database.", extra={LoggingExtras.FILE: filepath})

        # If the returned item's status is not set to complete, then field the filepath
        elif item[0].status != TableStatus.COMPLETE:
            logger.info(f"CSV file {os.path.basename(filepath)} has not yet been uploaded to the database.", extra={LoggingExtras.FILE: filepath})
            yield filepath

        # Raise an error for unhandled case
        else:
            logger.error("Unahndled case encountered during CSV upload check", extra={LoggingExtras.FILE: filepath})