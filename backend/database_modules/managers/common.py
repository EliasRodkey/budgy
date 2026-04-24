#!python3
"""
backend.database_modules.managers.common.py -
Contians shared functions and classes used by the database manager modules.

Functions:
    - convert_datetime_nums_to_range: Takes month and year as integers and converts them to a datetiem range.

Variables:
    - DB_FILE: The shared DatabaseFile object that will store all database tables used by this application
"""
# Standard library imports
from datetime import datetime, timedelta
from typing import Tuple, List

# Third party imports
import pandas as pd

# Custom imports
from pleasant_database import DatabaseFile

# Local imports
from backend.utils.analysis_utils import CategoriesEnum
from backend.utils.file_utils import EDirectories

# initialize module logger
import logging
logger = logging.getLogger(__name__)


DB_FILE = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)
    


class DuplicateError(Exception):
    """Raised when a duplicate filepath is detected in the table."""
    def __init__(self, entry, table, message="Duplicate entry:"):
        self.entry = entry
        self.table = table
        super().__init__(f"{message} {entry}")



def convert_datetime_nums_to_range(month: int | None, year: int | None) -> Tuple[datetime, datetime]:
    """
    Converts a given month and year integer into a datetime start and end range.
    
    Args:
        month (int): The month as an integer (1-12).
        year (int): The year as an integer (e.g., 2024).
    
    Returns:
        Tuple[datetime, datetime, str]: A tuple containing the start and end datetime objects for the specified month and year.
    """
    # Check to make sure the month and year are valid if not None
    if month is not None and (month < 1 or month > 12):
        logger.error(f"Invalid month value: {month}. Month should be between 1 and 12.")
        raise ValueError(f"Invalid month value: {month}. Month should be between 1 and 12.")

    if year is not None and (year < 2000 or year > datetime.now().year):
        logger.error(f"Invalid year value: {year}. Year should be between 2000 and the current year.")
        raise ValueError(f"Invalid year value: {year}. Year should be between 2000 and the current year.")

    # If month and year are not present return datetime from 2000 to now
    if not year and not month:
        return datetime(2000, 1, 1), datetime.now()

    # If no year is present use the current year
    if not year:
        year = datetime.now().year

    # If there is no month, set the start and end date to cover the whole year
    if not month:
        start_date = datetime(year, 1, 1)
        end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)

    elif month == 12:
        start_date = datetime(year, month, 1)
        end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)

    else:
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)

    return start_date, end_date


def format_column_names(column: pd.Series) -> pd.Series:
    """Takes the input columns (plain english) and converts them to lower case, snake case, and removes special characters"""
    column = column.str.strip()
    column = column.str.lower()
    column = column.str.replace(" ", "_")
    column = column.str.replace("&", "and")
    return column