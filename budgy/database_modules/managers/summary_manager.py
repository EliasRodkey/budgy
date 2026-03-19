#!python3
"""
budgy.database_modules.managers.summary_manager.py -
Module contianing functions for reading, writing, and updating values in the summary table.


"""
# Standard library imports

# Third party imports
import pandas as pd

# Custom imports
from local_db import DatabaseFile, DatabaseManager

# Local imports
from ..models.summaries import SummariesTable
from .transaction_manager import TransactionsTableManager

# initialize module logger
import logging
logger = logging.getLogger(__name__)



class SummariesTableManager(DatabaseManager):
    """"""
    def __init__(self, db_file: DatabaseFile):
        super().__init__(SummariesTable, db_file)

    
    def upload_monthly_summary(self, month: int, year: int, summary: pd.DataFrame) -> None:
        """
        Initiates a cleaning and upload of a provided summary from the transactions table from a the given month and year.

        Args:
            month (int): month given as an integer
            year (int): year given as an integer
            summary (pd.DataFrame): Monthly summary output from transactions table manager.
        """ 
        logger.info(f"Uploading monthly summary for {month} / {year} to {self.table_name}")

        if self._check_summary_exists(month, year):
            logger.warning(f"Entry for month = {month} and year = {year} already exists in {self.table_name}")
        
        else:
            clean_summary = self._clean_monthly_summary(summary)
            

    
    def update_summary(self, month: int, year: int):
        """
        """
        pass


    def _clean_monthly_summary(self, summary: pd.DataFrame) -> dict:
        """Cleans and validates monthly summary for upload"""
        columns = summary.columns


    def _check_summary_exists(self, month: int, year: int) -> bool:
        """Checks to see if a summary already exists in the summaries table from the given month and year"""
        logger.debug(f"Checking {self.table_name} for record from month = {month}, year = {year}")

        return_item = self.fetch_items_by_attribute(month=month, year=year)

        return return_item != []