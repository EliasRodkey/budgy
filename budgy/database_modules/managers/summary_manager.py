#!python3
"""
budgy.database_modules.managers.summary_manager.py -
Module contianing functions for reading, writing, and updating values in the summary table.


"""
# Standard library imports
from datetime import datetime

# Third party imports
import pandas as pd

# Custom imports
from pleasant_database import DatabaseFile, DatabaseManager, DatabaseIntegrityError, ItemNotFoundError

# Local imports
from budgy.utils.analysis_utils import PrimaryCategories, DetailedCategories, CATEGORY_MAPPING
from ..models.summaries import SummariesTable, summary_columns


# initialize module logger
import logging
logger = logging.getLogger(__name__)



class SummariesTableManager(DatabaseManager):
    """
    Class that allows interfacing with the summaries database table.

    Methods:
        - upload_monthly_summary: Initiates a cleaning and upload of a provided summary from the transactions table from a the given month and year.
        - update_summary: Updates a summary entry in the summaries table.
    """
    def __init__(self, db_file: DatabaseFile):
        super().__init__(SummariesTable, db_file)

    
    def upload_monthly_summary(self, month: int, year: int, summary: pd.DataFrame, budget_id: int=None) -> None:
        """
        Initiates a cleaning and upload of a provided summary from the transactions table from a the given month and year.

        Args:
            month (int): month given as an integer
            year (int): year given as an integer
            summary (pd.DataFrame): Monthly summary output from transactions table manager.
            budget_id (int): the id of the budget used to compare spending to, defaults to most recent if None.
        """
        logger.info(f"Uploading monthly summary for {month} / {year} to {self.table_name}")

        if self._check_summary_exists(month, year):
            logger.warning(f"Entry for month = {month} and year = {year} already exists in {self.table_name}, skipping.")
        
        else:
            clean_summary = self._clean_monthly_summary(month, year, summary, budget_id=budget_id)
        
            try:
                self.add_item(**clean_summary)

            except DatabaseIntegrityError:
                logger.warning(f"Trying to upload a duplicate summary for {month} / {year}, skipping")

            except Exception as e:
                logger.error(f"Unknown error encountered while uploading monthly summary for {month} / {year}: {e}")
                raise e


    def update_summary(self, month: int, year: int, summary: pd.DataFrame, budget_id: int=None):
        """
        Updates a summary entry in the summaries table. 
        Should be called when new transaction categories are updated in transactions db.

        Args:
            month (int): month given as an integer
            year (int): year given as an integer
            summary (pd.DataFrame): Monthly summary output from transactions table manager.
            budget_id (int): the id of the budget used to compare spending to, defaults to most recent if None.
        """
        logger.info(f"Updating monthly summary for {month} / {year} in {self.table_name}")

        if not self._check_summary_exists(month, year):
            logger.warning(f"Entry for month = {month} and year = {year} doesn't exists in {self.table_name}")

        else:
            clean_summary = self._clean_monthly_summary(month, year, summary, budget_id=budget_id)

            try:
                self.update_item(self._get_summary_id(month, year), **clean_summary)

            except DatabaseIntegrityError as e:
                logger.error(f"Summary table not updaes for {month} / {year}: {e}")


    def _clean_monthly_summary(self, month: int, year: int, summary: pd.DataFrame, budget_id: int=None) -> dict:
        """Cleans and validates monthly summary for upload, returns validated dict"""
        logger.debug(f"Cleaning monthly summary for uplaod...")
        input_columns = summary.columns
        if sum([col not in SummariesTable.get_column_names() for col in input_columns]) > 0:
            raise KeyError(f"Invalid column name in raw summary table {input_columns}")

        summary[SummariesTable.date.name] = datetime(year, month, 1)
        summary[SummariesTable.month.name] = month
        summary[SummariesTable.year.name] = year
        summary[SummariesTable.budget_id.name] = self._get_latest_budget_id() if budget_id is None else budget_id

        columns = summary.columns  # Capture after adding date/month/year so they're not overwritten
        summary_record = {}

        for col in summary_columns:
            if col.dest not in columns:
                logger.debug(f"Summary missing {col.dest}, adding...")
                summary[col.dest] = 0

            raw_value = summary[col.dest].max()
            if col.dest == SummariesTable.date.name:
                validated_entry = raw_value.to_pydatetime() if hasattr(raw_value, "to_pydatetime") else raw_value
            else:
                validated_entry = col.convert(raw_value)
            

            if col.dest == SummariesTable.month.name:
                assert 1 <= validated_entry <= 12, f"Invalid month entered into summary table record month = {validated_entry}"
            
            elif col.dest == SummariesTable.year.name:
                assert 2000 <= validated_entry <= datetime.now().year, f"Invalid year entered into summary table record month = {validated_entry}"
            
            elif col.dest == SummariesTable.date.name:
                assert isinstance(validated_entry, datetime), f"Invalid date entry for summary table: {validated_entry}, type: {type(validated_entry)}"

            elif col.dest == SummariesTable.budget_id.name:
                pass

            elif col.dest == SummariesTable.income.name or col.dest in [detailed.as_snake_case() for detailed in CATEGORY_MAPPING[PrimaryCategories.INCOME]]:
                assert validated_entry >= 0, f"Invalid value for {col.dest}: {validated_entry}"
                assert isinstance(validated_entry, float),f"Invalid value for {col.dest}: {validated_entry}, type: {type(validated_entry)}"
            
            else:
                assert isinstance(validated_entry, float),f"Invalid value for {col.dest}: {validated_entry}, type: {type(validated_entry)}"

            # TODO: Everything else besides maybe some transfers should be negative?
            summary_record[col.dest] = validated_entry
        
        return summary_record
        

    def _check_summary_exists(self, month: int, year: int) -> bool:
        """Checks to see if a summary already exists in the summaries table from the given month and year"""
        logger.debug(f"Checking {self.table_name} for record from month = {month}, year = {year}")

        return_item = self.fetch_items_by_attribute(month=month, year=year)
        return return_item != []
    

    def _get_summary_id(self, month: int, year: int) -> int:
        """Retrives the summary id of the assocaited month / year combo"""
        logger.debug(f"Fetching summaries.id for month = {month}, year = {year}")

        return_item = self.fetch_items_by_attribute(month=month, year=year)

        if return_item:
            return return_item[0].id

        else:
            raise ItemNotFoundError(float(f"{month}.{year}"), self.table_class)
    

    def _get_latest_budget_id(self) -> int:
        """Returns the budget_id from the most recently inserted summary record."""
        logger.debug(f"Checking latest summary upload for budget_id...")

        summaries = self.fetch_all_items()

        if not summaries:
            raise ItemNotFoundError("latest budget_id", self.table_class)

        latest = max(summaries, key=lambda s: s.id)
        return latest.budget_id
        