
# Standard library imports
from collections import namedtuple
from datetime import date, datetime
from enum import Enum

# Initialize module logger
import logging
logger = logging.getLogger(__name__)

Field = namedtuple('Column', 'src dest convert')



class TableStatus(str, Enum):
    """Enum class with different possible status' for the database records"""
    POSTED = "Posted"
    UNCHECKED = "Unchecked"
    COMPLETE = "Complete"
    INCOMPLETE = "Incomplete"

    def __str__(self):
        return str(self.value)



def parse_date(text) -> datetime:
    """Turns date in format "%Y-%m-%d" into datetime"""
    return datetime.strptime(text, "%Y-%m-%d")