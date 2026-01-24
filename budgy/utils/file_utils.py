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



class EDirectories(str, Enum):
    """
    Enum class for commonly used directory paths within the project

    Attributees:
        - LOG_DIR: Path to the logs directory.
    """
    LOG_DIR = os.path.join(os.getcwd(), "data", "logs")
    CSV_DIR = os.path.join(os.getcwd(), "data", "csv_downloads")
    DB_DIR = os.path.join(os.getcwd(), "data", "databases")
    DB_FILENAME = "database.db"


    def __str__(self):
        return str(self.value)



# Import logging utilities
import logging
from loggers import configure_logger, LoggingHandlerController

logger = logging.getLogger(__name__)
log_handlers: LoggingHandlerController = configure_logger(logger, EDirectories.LOG_DIR)


def get_csv_filenames() -> list[str]:
    """Reads the contents of the csv_downloads directory and returns a list of CSV filenames."""
    filenames = os.listdir(EDirectories.CSV_DIR)
    return [f for f in filenames if f.endswith('.csv')]


if __name__ == "__main__":
    print(get_csv_filenames())