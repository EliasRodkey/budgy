#!python3
"""
budgy.utils.tests.test_intake.test_csv

Tests for budgy.intake.csv module.
"""
# Standard library imports
import datetime
import os
import pytest
import sys

# Third-party imports
import pandas as pd

# Local imports
from budgy.intake.csv import iter_csv_file, columns, iter_csv_uploaded

# TODO: This should only test CSV ripping and data validation! may want to think about wrapping all of this under db_utils or a new pipeline module!
def test_iter_csv(clean_updates_database):
    for csv_filepath in iter_csv_uploaded(csv_directory=TEST_CSV_DIR, update_table_manager=clean_updates_database):
        for record in iter_csv_file(csv_filepath, columns):
            for col in columns:
                assert col.dest in record
            if record["amount"] > 0:
                assert record["status"] == "Unchecked"
            if col.dest == "authorized_date" or col.dest == "posted_date":
                assert isinstance(record[col.dest], datetime)