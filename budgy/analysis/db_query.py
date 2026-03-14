"""
"""

# Standard library imports
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, Generator, List, Tuple

# Custom imports
from local_db import DatabaseManager

# Local imports
from budgy.utils.analysis_utils import PrimaryCategories, DetailedCategories, CATEGORY_MAPPING, REVERSE_CATEGORY_MAPPING
from budgy.database_modules.managers.transaction_manager import transactions_table_manager
from budgy.database_modules.models.transactions import TransactionsTable
from budgy.utils.file_utils import LoggingExtras

# initialize module logger
import logging
logger = logging.getLogger(__name__)


def convert_datetime_nums_to_range(month: int, year: int) -> Tuple[datetime, datetime]:
    """
    Converts a given month and year integer into a datetime start and end range.
    
    Args:
        month (int): The month as an integer (1-12).
        year (int): The year as an integer (e.g., 2024).
    
    Returns:
        Tuple[datetime, datetime]: A tuple containing the start and end datetime objects for the specified month and year.
    """
    start_date = datetime(year, month, 1)

    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
    
    if month < 1 or month > 12:
        logger.error(f"Invalid month value: {month}. Month should be between 1 and 12.")
        raise ValueError(f"Invalid month value: {month}. Month should be between 1 and 12.")
    
    elif year < 2000 or year > datetime.now().year:
        logger.error(f"Invalid year value: {year}. Year should be between 2000 and the current year.")
        raise ValueError(f"Invalid year value: {year}. Year should be between 2000 and the current year.")

    return start_date, end_date


# Pull records by **kwargs, then convert to pandas dataframe.
def retrieve_records_by_attribute_over_period(month: int, year: int, db_manager: DatabaseManager=transactions_table_manager, **kwargs) -> pd.DataFrame:
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
        logger.exception(f"Unhandled error retrieving records for attributes: {kwargs} over period: {start_date} to {end_date}.")
        return pd.DataFrame()

    if not records:
        logger.warning(f"No records found for attributes: {kwargs} over period: {start_date} to {end_date}.")
    
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

    # Group the records by primary category and sum the amounts for a "total_amount"
    category_report = records_df.groupby(TransactionsTable.primary_category.name)[TransactionsTable.amount.name].sum().reset_index()
    category_report.rename(columns={TransactionsTable.amount.name: "total_amount"}, inplace=True)

    # Do the same thing on detailed_category

    # Concat two DFs along vertical axis

    # Transpose df and map column names to correct values (I think I have to do this ahead of time somehow)

    # Really should be doing all of this in jupyter!!

    logger.debug(f"Generated monthly category report for {month}/{year}:\n{category_report}")

    return category_report