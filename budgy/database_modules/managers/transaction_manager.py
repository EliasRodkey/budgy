#!python3
"""
budgy.database_modules.managers.transactino_manager.py - 
Module contianing functions for reading, writing, and updating values in the transactions and updates tables.

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

# Third party imports
import pandas as pd

# Custom imports
from local_db import DatabaseFile, DatabaseManager, DuplicateError

# Local imports
from budgy.database_modules.managers.common import DB_FILE, convert_datetime_nums_to_range, format_column_names
from budgy.database_modules.models.common import TableStatus
from budgy.database_modules.models.transactions import TransactionsTable, UpdatesTable
from budgy.utils.analysis_utils import PrimaryCategories, DetailedCategories
from budgy.utils.file_utils import EDirectories, LoggingExtras, get_csv_filenames

# initialize module logger
import logging
logger = logging.getLogger(__name__)

# Table managers
transactions_table_manager = DatabaseManager(TransactionsTable, DB_FILE)
update_table_manager = DatabaseManager(UpdatesTable, DB_FILE)


# =========================Transactions DB Upload Funcitons===================================

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


# =========================Transactions DB Download Funcitons===================================


# Pull records by **kwargs, then convert to pandas dataframe.
def retrieve_records_by_attribute_over_period(month: int, year: int, 
                                              db_manager: DatabaseManager=transactions_table_manager, 
                                               **kwargs) -> pd.DataFrame:
    """
    Retrieves all records from the database associated with the given Database Manager that match the specified attributes and fall within the specified date range.
    Avoids pulling excluded transactions by filtering them out.

    Args:
        month (int): The month as an integer (1-12).
        year (int): The year as an integer (e.g., 2024).
        db_manager (DatabaseManager, optional): The Database Manager instance to use for querying the database. Defaults to transactions_table_manager.
        **kwargs: Arbitrary keyword arguments representing the attributes to filter records by (e.g., primary_category='Food', detailed_category='Groceries').

    Returns:
        List[BaseTable]: A list of records that match the specified attributes and date range.
    """
    start_date, end_date = convert_datetime_nums_to_range(month, year)

    logger.debug(
        f"Retrieving records from {start_date} to {end_date} with attributes: {kwargs} using manager: {db_manager}", 
        extra={
            LoggingExtras.START_DATE.value: start_date.strftime(LoggingExtras.DATETIME_FORMAT), 
            LoggingExtras.END_DATE.value: end_date.strftime(LoggingExtras.DATETIME_FORMAT), 
            LoggingExtras.ATTRIBUTES.value: kwargs
        }
    )

    attributes = {k: ("==", v) for k, v in kwargs.items()}
    attributes[TransactionsTable.authorized_date.name] = [(">=", start_date), ("<=", end_date)]
    attributes[TransactionsTable.exclude.name] = ("==", False) # Ensure we only retrieve transactions that are not marked as excluded
        
    try:
        records = db_manager.filter_items(attributes)

    except Exception:
        logger.exception(f"Unhandled error retrieving records for attributes: {attributes} over period: {start_date} to {end_date}.")
        return pd.DataFrame()

    if not records:
        logger.warning(f"No records found over period with specified attributes: {start_date} to {end_date}.", extra={LoggingExtras.ATTRIBUTES: attributes})
    
    return db_manager.convert_orm_list_to_dataframe(records)


def generate_monthly_category_report(month: int, year: int, db_manager: DatabaseManager=transactions_table_manager) -> pd.DataFrame:
    """
    Generates a monthly category report for the specified month and year, summarizing the total amount spent in each category.

    Args:
        month (int): The month as an integer (1-12).
        year (int): The year as an integer (e.g., 2024).
        db_manager (DatabaseManager, optional): The Database Manager instance to use for querying the database. Defaults to transactions_table_manager.

    Returns:
        pd.DataFrame: A DataFrame containing the total amount spent in each primary category for the specified month and year.
    """
    logger.info(f"Generating monthly category report for month/year: {month}/{year} using manager: {db_manager}.")

    records_df = retrieve_records_by_attribute_over_period(month, year, db_manager)
    # TODO: Move this to db_models, will be the headers for new SummaryTable object.
    columns = [member.name.lower().replace(" ", "_") for member in PrimaryCategories] + \
                [member.name.lower().replace(" ", "_")  for member in DetailedCategories] + \
                    ["total_amount"]
    
    if records_df.empty:
        logger.info(f"No transactions found for month/year: {month}/{year}. Returning empty report.")
        return pd.DataFrame(columns=columns)

    # Group the records by primary category and detailed category seperately and sum.
    primary_category_report = records_df.groupby(TransactionsTable.primary_category.name)[TransactionsTable.amount.name].sum().reset_index()
    detailed_category_report = records_df.groupby(TransactionsTable.detailed_category.name)[TransactionsTable.amount.name].sum().reset_index()

    # Prepare both dataframes for concatenation by aligning the columns
    primary_category_report.columns = ["category", "total"]
    detailed_category_report.columns = ["category", "total"]

    # Concat two DFs along vertical axis
    category_report = pd.concat([primary_category_report, detailed_category_report], axis=0).reset_index()

    # from pprint import pprint

    # print("records orient")
    # records_dict = category_report.to_dict(orient="records")
    # pprint(records_dict)

    # print("list orient")
    # list_dict = category_report.to_dict(orient="list")
    # pprint(list_dict)

    # print("index orient")
    # index_dict = category_report.to_dict(orient="index")
    # pprint(index_dict)

    # Convert category names to python friendly column names
    category_report.category = format_column_names(category_report.category)
    category_report.set_index("category", inplace=True)
    category_report = category_report.T
    category_report["new_category"] = 0
    # Transpose df and map column names to correct values (I think I have to do this ahead of time somehow)

    # Really should be doing all of this in jupyter!!

    logger.debug(f"Generated monthly category report for {month}/{year}:\n{category_report}")

    return category_report
