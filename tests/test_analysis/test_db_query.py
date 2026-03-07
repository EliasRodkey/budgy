"""
"""

# Standard library imports
from datetime import datetime
import os
import pandas as pd

# Local imports
from budgy.analysis.db_query import convert_datetime_nums_to_range, retrieve_records_by_attribute_over_period, generate_monthly_category_report
from budgy.utils.analysis_utils import PrimaryCategories, DetailedCategories
from tests.conftest import TEST_CSV_DIR, full_transactions_database

# Initialize module logger
import logging
logger = logging.getLogger(__name__)

def test_generate_monthly_category_report(full_transactions_database):
    """Test the generate_monthly_category_report function for a specific month and year."""
    month = 12
    year = 2025

    report_df = generate_monthly_category_report(month, year, full_transactions_database)

    # Check that the report is a DataFrame and has the expected columns
    assert isinstance(report_df, pd.DataFrame), "Report should be a pandas DataFrame."
    expected_columns = [member.name.lower().replace(" ", "_") for member in PrimaryCategories] + \
                       [member.name.lower().replace(" ", "_") for member in DetailedCategories] + \
                       ["total_amount"]
    assert all(col in report_df.columns for col in expected_columns), f"Report should contain the expected columns: {expected_columns}"
