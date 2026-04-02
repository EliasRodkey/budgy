#!python3
"""
budgy.database_modules.managers.summary_manager.py -
Module contianing functions for reading, writing, and updating values in the summary table.

Classes:
    - SummariesTableManager: DatabaseManager subclass for the SummariesTable.
"""
# Standard library imports
from datetime import datetime
from typing import List

# Third party imports
import pandas as pd

# Custom imports
from pleasant_database import DatabaseFile, DatabaseManager, DatabaseIntegrityError, ItemNotFoundError

# Local imports
from budgy.utils.analysis_utils import PrimaryCategories, DetailedCategories, CATEGORY_MAPPING
from budgy.utils.file_utils import LoggingExtras
from .common import convert_datetime_nums_to_range
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
        - fetch_summary_by_id: Retrieves a monthly summary from the sumaries table with the given summary_id.
        - fetch_summaries_over_period: Retrieves all records from the summaries table that fall within the specified date range.
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


    def update_summary(self, month: int, year: int, summary: pd.DataFrame,):
        """
        Updates a summary entry in the summaries table. 
        Should be called when new transaction categories are updated in transactions db.

        Args:
            month (int): month given as an integer
            year (int): year given as an integer
            summary (pd.DataFrame): Monthly summary output from transactions table manager.
        """
        logger.info(f"Updating monthly summary for {month} / {year} in {self.table_name}")

        if not self._check_summary_exists(month, year):
            logger.warning(f"Entry for month = {month} and year = {year} doesn't exists in {self.table_name}")

        else:
            summary_id = self._get_summary_id(month, year)
            summary_record = self.fetch_summary_by_id(summary_id)
            clean_summary = self._clean_monthly_summary(month, year, summary, budget_id=summary_record.budget_id)

            try:
                self.update_item(summary_id, **clean_summary)

            except DatabaseIntegrityError as e:
                logger.error(f"Summary {summary_id} not updated for {month} / {year}: {e}")
    

    def update_summary_budget_id(self, month: int, year: int, budget_id: int) -> None:
        """Updates the budget id associated with the month year combination provided."""
        logger.info(f"Updating summary {month} /{year} budget id to: {budget_id}")

        summary_id = self._get_summary_id(month, year)

        try:
            self.update_item(summary_id, budget_id=budget_id)
        
        except DatabaseIntegrityError as e:
                logger.error(f"Summary {summary_id} budget id not updated for {month} / {year}: {e}")


    def fetch_summary_by_id(self, summary_id: int) -> SummariesTable:
        """Retrieves a monthly summary from the summariestable with the given summary_id."""
        logger.info(f"Retrieving summary {summary_id} from {self.table_name}")

        try:
            return self.fetch_item_by_id(summary_id)
        
        except ItemNotFoundError:
            logger.warning(f"No budget exists with ID {summary_id}")
            return SummariesTable
        
        except Exception as e:
            logger.error(f"Unknown exception occured retrieving budget {summary_id}: {e}")
            raise
    

    def fetch_summaries_over_period(self, month: int=None, year: int=None) -> List[SummariesTable]:
        """
        Retrieves all records from the summaries table that match the specified attributes
        and fall within the specified date range.

        Args:
            month (int): The month as an integer (1-12).
            year (int): The year as an integer (e.g., 2024).
        """
        logger.info(f"Retrieving summaries from {year} from {self.table_name}")

        start_date, end_date = convert_datetime_nums_to_range(month, year)

        logger.debug(
            f"Retrieving records from {start_date} to {end_date} using manager: {self}",
            extra={
                LoggingExtras.START_DATE.value: start_date.strftime(LoggingExtras.DATETIME_FORMAT),
                LoggingExtras.END_DATE.value: end_date.strftime(LoggingExtras.DATETIME_FORMAT),
            }
        )

        attributes = {}
        attributes[SummariesTable.date.name] = [(">=", start_date), ("<=", end_date)]

        try:
            records = self.filter_items(attributes)

        except Exception as e:
            logger.exception(f"Unhandled error retrieving records for attributes: {attributes} over period: {start_date} to {end_date}")
            return pd.DataFrame()

        if not records:
            logger.warning(f"No records found over period with specified attributes: {start_date} to {end_date}.", extra={LoggingExtras.ATTRIBUTES: attributes})

        return self.convert_orm_list_to_dataframe(records)
    

    def calculate_total_spending_over_period(self, month: int=None, year: int=None) -> pd.DataFrame:
        """Calculates total spending over a given period by summing all category columns in the summary table."""
        logger.info(f"Calculating total spending over period: {month} / {year} from {self.table_name}")

        summaries_df = self.fetch_summaries_over_period(month, year)

        if summaries_df.empty:
            logger.warning(f"No summaries found for period: {month} / {year}, returning empty DataFrame.")
            return summaries_df
        
        all_categories = PrimaryCategories.as_snake_case_headers() + DetailedCategories.as_snake_case_headers()
        spending_df = summaries_df[all_categories].copy()
        
        return spending_df.sum(axis=1)
    

    def calculate_average_total_spending_over_period(self, month: int=None, year: int=None) -> pd.DataFrame:
        """Calculates total spending over a given period by summing all category columns in the summary table."""
        logger.info(f"Calculating total spending over period: {month} / {year} from {self.table_name}")

        summaries_df = self.fetch_summaries_over_period(month, year)

        if summaries_df.empty:
            logger.warning(f"No summaries found for period: {month} / {year}, returning empty DataFrame.")
            return summaries_df
        
        all_categories = PrimaryCategories.as_snake_case_headers() + DetailedCategories.as_snake_case_headers()
        spending_df = summaries_df[all_categories].copy()
        
        return spending_df.mean(axis=1)


    def _clean_monthly_summary(self, month: int, year: int, summary: pd.DataFrame, budget_id: int=None) -> dict:
        """Cleans and validates monthly summary for upload, returns validated dict"""
        logger.debug(f"Cleaning monthly summary for uplaod...")

        flat_summary = self._flatten_summary(summary)

        input_columns = summary.columns
        if sum([col not in SummariesTable.get_column_names() for col in input_columns]) > 0:
            raise KeyError(f"Invalid column name in raw summary table {input_columns}")

        summary[SummariesTable.date.name] = datetime(year, month, 1)
        summary[SummariesTable.month.name] = month
        summary[SummariesTable.year.name] = year
        summary[SummariesTable.budget_id.name] = self._get_latest_budget_id() if budget_id is None else budget_id

        columns = list(summary.columns)  # Capture after adding date/month/year so they're not overwritten
        summary_record = {}

        for col in summary_columns:
            if col.dest not in columns:
                logger.debug(f"Summary missing {col.dest}, adding...")
                summary[col.dest] = 0
                columns.append(col.dest) # Add updated columns to list so we don't try to add them again later

            raw_value = summary[col.dest].max()
            if col.dest == SummariesTable.date.name:
                validated_entry = raw_value.to_pydatetime() if hasattr(raw_value, "to_pydatetime") else raw_value
            else:
                # TODO: For some reason when we get to "other" here, we have 2 columns and it throws an error for trying to convert the series.
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


    def _flatten_summary(self, summary: pd.DataFrame) -> pd.DataFrame:
        """Flattens the summary dataframe for upload to the summaries table."""
        sum_column = summary["sum"]
        mean_column = summary["mean"]
        count_column = summary["count"]

        sum_column.index = self._attach_column_prefix(sum_column.index, "sum")
        mean_column.index = self._attach_column_prefix(mean_column.index, "mean")
        count_column.index = self._attach_column_prefix(count_column.index, "count")

        return pd.concat([sum_column, mean_column, count_column], axis=1).reset_index().T
    
    def _attach_column_prefix(self, column: pd.Series, prefix: str) -> pd.Series:
        """Attaches a prefix to a column name for upload to the summaries table."""
        return column.rename(f"{prefix}_{column.name}")
        