#!python3
"""
budgy.database_modules.managers.common.py -
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
from local_db import DatabaseFile

# Local imports
from budgy.utils.file_utils import EDirectories

# initialize module logger
import logging
logger = logging.getLogger(__name__)


DB_FILE = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)


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


def format_column_names(column: pd.Series) -> pd.Series:
    """Takes the input columns (plain english) and converts them to lower case, snake case, and removes special characters"""
    column = column.str.strip()
    column = column.str.lower()
    column = column.str.replace(" ", "_")
    column = column.str.replace("&", "and")
    return column