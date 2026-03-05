"""
"""

# Standard library imports
from datetime import datetime
import pandas as pd
from typing import Dict, Generator, List

# Local imports
from local_db import DatabaseManager
from budgy.utils.db_models import TransactionsTable, transactions_table_manager
from budgy.utils.file_utils import LoggingExtras

# initialize module logger
import logging
logger = logging.getLogger(__name__)


# TODO: This is inefficient, db manager basically already does this, functions should combine functionality to return more helpful info.

# Pull records by **kwargs, then convert to pandas dataframe.
def retrieve_records_by_attribute_over_period(start_date: str, end_date: str, db_manager: DatabaseManager=transactions_table_manager, **kwargs) -> pd.DataFrame:
    """
    Retrieves all records from the database associated with the given Database Manager that match the specified attributes and fall within the specified date range.

    Args:
        start_date (str): The start date of the period to filter records by (inclusive).
        end_date (str): The end date of the period to filter records by (inclusive).
        db_manager (DatabaseManager, optional): The Database Manager instance to use for querying the database. Defaults to transactions_table_manager.
        **kwargs: Arbitrary keyword arguments representing the attributes to filter records by (e.g., primary_category='Food', detailed_category='Groceries').

    Returns:
        List[BaseTable]: A list of records that match the specified attributes and date range.
    """
    logger.debug(f"Retrieving records from {start_date} to {end_date} with attributes: {kwargs} using manager: {db_manager}", extra={LoggingExtras.START_DATE: start_date, LoggingExtras.END_DATE: end_date, LoggingExtras.ATTRIBUTES: kwargs})

    attributes = {k: ("==", v) for k, v in kwargs.items()}
    attributes[TransactionsTable.timestamp.name] = (">=", start_date)
    attributes[TransactionsTable.timestamp.name] = ("<=", end_date)

    try:
        records = db_manager.filter_items(attributes)

    except Exception:
        logger.exception(f"Unhandled error retrieving records for attributes: {kwargs} over period: {start_date} to {end_date}.")
        return pd.DataFrame()

    if not records:
        logger.warning(f"No records found for attributes: {kwargs} over period: {start_date} to {end_date}.")
    
    return db_manager.convert_orm_list_to_dataframe(records)