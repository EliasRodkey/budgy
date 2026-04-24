#!python3
"""
tests.test_database_modules.test_managers.test_common

Tests for backend.database_modules.managers.common — convert_datetime_nums_to_range and format_column_names.
"""
# Standard library imports
from datetime import datetime, timedelta

# Third party imports
import pandas as pd
import pytest

# Local imports
from backend.database_modules.managers.common import convert_datetime_nums_to_range, format_column_names

# Initialize module logger
import logging
logger = logging.getLogger(__name__)


# =========================convert_datetime_nums_to_range===================================

def test_convert_range_both_none():
    """Both month and year None → returns (datetime(2000,1,1), ~now)."""
    start, end = convert_datetime_nums_to_range(None, None)
    assert start == datetime(2000, 1, 1)
    # end should be approximately now (within a few seconds)
    assert abs((end - datetime.now()).total_seconds()) < 5


def test_convert_range_year_only():
    """year=2024, month=None → Jan 1 2024 to Dec 31 2024 23:59:59."""
    start, end = convert_datetime_nums_to_range(None, 2024)
    assert start == datetime(2024, 1, 1)
    assert end == datetime(2025, 1, 1) - timedelta(seconds=1)


def test_convert_range_month_only():
    """month=3, year=None → March 1 to March 31 23:59:59 in the current year."""
    current_year = datetime.now().year
    start, end = convert_datetime_nums_to_range(3, None)
    assert start == datetime(current_year, 3, 1)
    assert end == datetime(current_year, 4, 1) - timedelta(seconds=1)


def test_convert_range_specific_month_and_year():
    """month=6, year=2025 → June 1 to June 30 23:59:59 2025."""
    start, end = convert_datetime_nums_to_range(6, 2025)
    assert start == datetime(2025, 6, 1)
    assert end == datetime(2025, 7, 1) - timedelta(seconds=1)


def test_convert_range_december():
    """month=12, year=2025 → Dec 1 2025 to Dec 31 2025 23:59:59 (year rolls over correctly)."""
    start, end = convert_datetime_nums_to_range(12, 2025)
    assert start == datetime(2025, 12, 1)
    assert end == datetime(2026, 1, 1) - timedelta(seconds=1)


def test_convert_range_january():
    """month=1, year=2024 → Jan 1 to Jan 31 23:59:59 2024."""
    start, end = convert_datetime_nums_to_range(1, 2024)
    assert start == datetime(2024, 1, 1)
    assert end == datetime(2024, 2, 1) - timedelta(seconds=1)


def test_convert_range_year_boundary():
    """year=2000 (minimum allowed) returns a valid range."""
    start, end = convert_datetime_nums_to_range(None, 2000)
    assert start == datetime(2000, 1, 1)
    assert end == datetime(2001, 1, 1) - timedelta(seconds=1)


def test_convert_range_end_is_after_start():
    """For any valid input, end_date > start_date."""
    cases = [
        (None, None),
        (None, 2022),
        (5, None),
        (3, 2023),
        (12, 2024),
    ]
    for month, year in cases:
        start, end = convert_datetime_nums_to_range(month, year)
        assert end > start, f"end <= start for month={month}, year={year}"


def test_convert_range_invalid_month_zero():
    """month=0 raises ValueError."""
    with pytest.raises(ValueError, match="Invalid month"):
        convert_datetime_nums_to_range(0, 2025)


def test_convert_range_invalid_month_thirteen():
    """month=13 raises ValueError."""
    with pytest.raises(ValueError, match="Invalid month"):
        convert_datetime_nums_to_range(13, 2025)


def test_convert_range_invalid_month_negative():
    """Negative month raises ValueError."""
    with pytest.raises(ValueError, match="Invalid month"):
        convert_datetime_nums_to_range(-1, 2025)


def test_convert_range_invalid_year_too_old():
    """year=1999 (below 2000) raises ValueError."""
    with pytest.raises(ValueError, match="Invalid year"):
        convert_datetime_nums_to_range(None, 1999)


def test_convert_range_invalid_year_future():
    """year beyond current year raises ValueError."""
    future_year = datetime.now().year + 1
    with pytest.raises(ValueError, match="Invalid year"):
        convert_datetime_nums_to_range(None, future_year)


def test_convert_range_returns_tuple():
    """convert_datetime_nums_to_range returns a 2-tuple of datetimes."""
    result = convert_datetime_nums_to_range(6, 2024)
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], datetime)
    assert isinstance(result[1], datetime)


# =========================format_column_names===================================

def test_format_column_names_lowercase():
    """Uppercase letters are lowercased."""
    series = pd.Series(["FOOD", "INCOME"])
    result = format_column_names(series)
    assert list(result) == ["food", "income"]


def test_format_column_names_spaces_to_underscores():
    """Spaces are replaced with underscores."""
    series = pd.Series(["Food and Drink", "Health and Wellness"])
    result = format_column_names(series)
    assert list(result) == ["food_and_drink", "health_and_wellness"]


def test_format_column_names_ampersand_to_and():
    """Ampersands are replaced with 'and'."""
    series = pd.Series(["Food & Drink", "Government & Charity"])
    result = format_column_names(series)
    assert list(result) == ["food_and_drink", "government_and_charity"]


def test_format_column_names_strip_whitespace():
    """Leading and trailing whitespace is stripped."""
    series = pd.Series(["  income  ", " food "])
    result = format_column_names(series)
    assert list(result) == ["income", "food"]


def test_format_column_names_combined():
    """All transformations applied together: strip, lowercase, spaces→underscores, &→and."""
    series = pd.Series(["  Food & Drink  ", "  Housing & Utilities  "])
    result = format_column_names(series)
    assert list(result) == ["food_and_drink", "housing_and_utilities"]


def test_format_column_names_already_clean():
    """Already-clean snake_case strings pass through unchanged."""
    series = pd.Series(["income", "food_and_drink"])
    result = format_column_names(series)
    assert list(result) == ["income", "food_and_drink"]


def test_format_column_names_returns_series():
    """format_column_names returns a pd.Series."""
    series = pd.Series(["Income"])
    result = format_column_names(series)
    assert isinstance(result, pd.Series)
