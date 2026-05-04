
# Standard library imports
from collections import namedtuple
from datetime import date, datetime
from enum import Enum

# Initialize module logger
from pleasant_loggers import get_logger
logger = get_logger(__name__)

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
    """Parses date strings in common formats from bank/financial CSV exports."""
    for fmt in (
        "%Y-%m-%d",    # 2026-01-15 (ISO)
        "%m/%d/%Y",    # 01/15/2026 or 1/15/2026 (US)
        "%m/%d/%y",    # 01/15/26 or 1/15/26 (US short year)
        "%d/%m/%Y",    # 15/01/2026 (international)
        "%d/%m/%y",    # 15/01/26 (international short year)
        "%Y/%m/%d",    # 2026/01/15 (alternative ISO)
        "%m-%d-%Y",    # 01-15-2026 (US with dashes)
        "%m-%d-%y",    # 01-15-26 (US short year with dashes)
        "%d-%m-%Y",    # 15-01-2026 (international with dashes)
        "%d-%m-%y",    # 15-01-26 (international short year with dashes)
    ):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {text!r}")