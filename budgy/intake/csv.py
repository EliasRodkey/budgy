#! python3
"""
budgy.intake.csv
Reads data from raw SoFi CSV exports. Validates and exports data to local transactions database. 

Classes:
    - 

Functions:
    - 
"""

# Standard library imports
from collections import namedtuple
import datetime
from typing import Generator

# Local application imports
from ..utils.db_utils import updates_table_manager
from ..utils.file_utils import get_csv_filenames

# Initialize module logger
import logging
logger = logging.getLogger(__name__)


# Check whether or not the CSV data file has been uploaded to the database
def iter_csv_uploaded() -> Generator:
    """Iterates through the CSV files in the csv_downlaods directory and checks whether or not they have been uploaded to the database."""
    for file_name in get_csv_filenames():
        item = updates_table_manager.fetch_items_by_attribute(False, filename=file_name)
        if item != []:
            logger.info("CSV file has already been uploaded to the database.", extra={"file_name": file_name})
        else:
            logger.info("CSV file has not yet been uploaded to the database.", extra={"file_name": file_name})
            yield file_name



# Select CSV Files that have not yet been uploaded

# Import CSV data

# Define database structure and schema
Column = namedtuple("Src Colum Name", "Dest Column Name")

# Validate data for database insertion

# Insert data into database, checking to make sure it is not a duplicate


