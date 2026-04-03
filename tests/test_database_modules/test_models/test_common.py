#!python3
"""
tests.test_database_modules.test_models.test_common

Tests for budgy.database_modules.models.common — Column namedtuple, TableStatus enum, and parse_date helper.
"""
# Standard library imports
from datetime import datetime

# Third party imports
import pytest

# Local imports
from backend.database_modules.models.common import Field, TableStatus, parse_date

# Initialize module logger
import logging
logger = logging.getLogger(__name__)


# =========================parse_date===================================

def test_parse_date_valid():
    """parse_date returns the correct datetime for a well-formed string."""
    result = parse_date("2024-01-15")
    assert result == datetime(2024, 1, 15)


def test_parse_date_first_of_year():
    """parse_date correctly parses January 1st."""
    result = parse_date("2025-01-01")
    assert result == datetime(2025, 1, 1)


def test_parse_date_last_day_of_year():
    """parse_date correctly parses December 31st."""
    result = parse_date("2023-12-31")
    assert result == datetime(2023, 12, 31)


def test_parse_date_invalid_inputs():
    """parse_date raises ValueError for wrong format, non-date strings, and slash separators."""
    with pytest.raises(ValueError):
        parse_date("01/15/2024")
    with pytest.raises(ValueError):
        parse_date("not-a-date")
    with pytest.raises(ValueError):
        parse_date("2024/01/15")


# =========================TableStatus===================================

def test_table_status_all_values_present():
    """TableStatus contains all four expected members."""
    names = {member.name for member in TableStatus}
    assert names == {"POSTED", "UNCHECKED", "COMPLETE", "INCOMPLETE"}


def test_table_status_string_values():
    """Each TableStatus member has the correct string value."""
    assert TableStatus.POSTED.value == "Posted"
    assert TableStatus.UNCHECKED.value == "Unchecked"
    assert TableStatus.COMPLETE.value == "Complete"
    assert TableStatus.INCOMPLETE.value == "Incomplete"


def test_table_status_str():
    """str() on a TableStatus member returns its string value."""
    assert str(TableStatus.COMPLETE) == "Complete"
    assert str(TableStatus.INCOMPLETE) == "Incomplete"
    assert str(TableStatus.POSTED) == "Posted"
    assert str(TableStatus.UNCHECKED) == "Unchecked"


def test_table_status_is_string_subclass():
    """TableStatus inherits from str, so members compare equal to their string values."""
    assert TableStatus.COMPLETE == "Complete"
    assert TableStatus.POSTED == "Posted"


# =========================Column namedtuple===================================

def test_column_namedtuple_creation():
    """Column namedtuple can be created with src, dest, and convert fields."""
    col = Field("Source Header", "dest_column", str)
    assert col.src == "Source Header"
    assert col.dest == "dest_column"
    assert col.convert == str


def test_column_namedtuple_with_lambda():
    """Column namedtuple works with a lambda as the converter."""
    converter = lambda x: int(x)
    col = Field("Amount", "amount", converter)
    assert col.convert("42") == 42


def test_column_namedtuple_with_float():
    """Column namedtuple with float converter correctly converts strings."""
    col = Field("Amount", "amount", float)
    assert col.convert("99.95") == pytest.approx(99.95)


def test_column_namedtuple_missing_args():
    """Column namedtuple raises TypeError when created with missing arguments."""
    with pytest.raises(TypeError):
        Field("only_one_arg")


def test_column_namedtuple_indexing():
    """Column namedtuple fields are accessible by both name and index."""
    col = Field("src_val", "dest_val", int)
    assert col[0] == "src_val"
    assert col[1] == "dest_val"
    assert col[2] == int
