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
import datetime

# Import logging utilities
import logging
from loggers import configure_logger
from ..utils.file_utils import EDirectories

# Initialize logger
logger = logging.getLogger(__name__)
configure_logger(logger, log_direcotry=EDirectories.LOG_DIR)

# Check whether or not the CSV data file has been uploaded to the database
# Select CSV Files that have not yet been uploaded
# Import CSV data
# Define database structure and schema
# Validate data for database insertion
# Insert data into database, checking to make sure it is not a duplicate


