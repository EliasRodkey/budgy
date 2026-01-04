#!python3
"""
file_utils.py
Contains:
    - utility functions for file operations.
    - directory path enum

"""

from enum import Enum
import os



class EDirectories(str, Enum):
    """
    Enum class for commonly used directory paths within the project

    Attributees:
        - LOG_DIR: Path to the logs directory.
    """
    LOG_DIR = os.path.join(os.getcwd(), "budgy", "data", "logs")
    CSV_DIR = os.path.join(os.getcwd(), "budgy", "data", "csv_downloads")
    DB_DIR = os.path.join(os.getcwd(), "budgy", "data", "databases")


    def __str__(self):
        return str(self.value)



from budgy import ELF, Logger

_logger = Logger("file_utils", EDirectories.LOG_DIR)
_logger.add_file_handler(ELF.FORMAT_LOGGER_NAME)


def get_csv_filenames() -> list[str]:
    """Reads the contents of the csv_downloads directory and returns a list of CSV filenames."""
    filenames = os.listdir(EDirectories.CSV_DIR)
    return [f for f in filenames if f.endswith('.csv')]


if __name__ == "__main__":
    print(get_csv_filenames())