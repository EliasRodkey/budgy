
# Standard library imports
from collections import namedtuple
from enum import Enum



Column = namedtuple('Column', 'src dest convert')



class TableStatus(str, Enum):
    """Enum class with different possible status' for the database records"""
    POSTED = "Posted"
    UNCHECKED = "Unchecked"
    COMPLETE = "Complete"
    INCOMPLETE = "Incomplete"

    def __str__(self):
        return str(self.value)