#!python3
"""
file_utils.py
Contains:
    - utility functions for file operations.
    - directory path enum

"""

# Standard library importss
from enum import Enum
import os


# Consider switching to using pathlib Path objects here!
class EDirectories(str, Enum):
    """
    Enum class for commonly used directory paths within the project

    Attributees:
        - LOG_DIR: Path to the logs directory.
        - CSV_DIR: Path to the directory containing csv downloads
        - DB_DIR: path to the directory containing the database file
        - DB_FILENAME: Name of the database file that stores transaction values
        - DB_FILEPATH: File path directly to the DB file location.
    """
    LOG_DIR = os.path.join(os.getcwd(), "data", "logs")
    CSV_DIR = os.path.join(os.getcwd(), "data", "csv_downloads")
    DB_DIR = os.path.join(os.getcwd(), "data", "databases")
    DB_FILENAME = "budgy_financial_transaction.db"
    DB_FILEPATH = os.path.join(DB_DIR, DB_FILENAME)

    def __str__(self):
        return str(self.value)



# NOTE: this should really live in the logging package for consistency!
class LoggingExtras(str, Enum):
    """Enum class that stores extra params used commonly in logging"""
    FILE = "file"
    RECORD = "record"
    UPLOAD = "csv_upload"
    BASE_HASH = "base_hash"
    UQ_HASH = "uq_hash"



# Initialize module logger
import logging
logger = logging.getLogger(__name__)


def get_csv_filenames(csv_directory: str=EDirectories.CSV_DIR) -> list[str]:
    """Reads the contents of the csv_downloads directory and returns a list of CSV filenames."""
    filenames = os.listdir(csv_directory)
    return [os.path.join(os.getcwd(), csv_directory, f) for f in filenames if f.endswith('.csv')]


if __name__ == "__main__":
    print(get_csv_filenames())