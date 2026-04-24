#!python3
"""
backend.database_modules.managers.summary_manager.py -
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
from backend.utils.analysis_utils import PrimaryCategories, DetailedCategories
from backend.utils.file_utils import LoggingExtras
from .common import convert_datetime_nums_to_range
from ..models.summaries import SummariesTable



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
    

    # TODO: Make sure we are fetching only the data we plan on using. If not we need more specific fetch functions.
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


    def _clean_monthly_summary(self, month: int, year: int, summary: pd.DataFrame, budget_id: int=None) -> dict:
        """Validates and flattens a sparse monthly summary DataFrame for DB insertion.

        Args:
            month: Month as integer (1-12).
            year: Year as integer (2000–current).
            summary: Sparse DataFrame from generate_monthly_summary — index=categories, columns=['sum', 'mean', 'count'].
            budget_id: Budget to associate with this summary. Defaults to most recently inserted summary's budget_id.

        Returns:
            Dict with required scalar fields (date, month, year, budget_id) plus sparse sum_*/mean_*/count_* keys.
            DB column defaults fill any missing category columns.

        Raises:
            KeyError: If any category in the summary index is not a known primary or detailed category.
            AssertionError: If month/year are out of range, or income is negative.
        """
        logger.debug(f"Cleaning monthly summary for upload...")

        assert 1 <= month <= 12, f"Invalid month: {month}"
        assert 2000 <= year <= datetime.now().year, f"Invalid year: {year}"

        flat = self._flatten_summary(summary)

        all_known = set(PrimaryCategories.as_snake_case_headers() + DetailedCategories.as_snake_case_headers())
        for key in flat:
            category = key.split("_", 1)[1]  # strip 'sum_' / 'mean_' / 'count_' prefix
            if category not in all_known:
                raise KeyError(f"Unknown category in summary: '{category}'")

        income_sum = flat.get(f"sum_{PrimaryCategories.INCOME.as_snake_case()}", 0.0)
        assert income_sum >= 0, f"Income sum must be non-negative, got {income_sum}"

        flat[SummariesTable.date.name] = datetime(year, month, 1)
        flat[SummariesTable.month.name] = month
        flat[SummariesTable.year.name] = year
        flat[SummariesTable.budget_id.name] = self._get_latest_budget_id() if budget_id is None else budget_id

        return flat
        

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


    def _flatten_summary(self, summary: pd.DataFrame) -> dict:
        """Flattens a sparse summary DataFrame into a prefixed dict for DB insertion.

        Args:
            summary: DataFrame with index=category names, columns=['sum', 'mean', 'count'].

        Returns:
            Dict with keys like 'sum_income', 'mean_income', 'count_income' for each row present.
            Values are native Python float/int (not numpy types) to satisfy pleasant_database type checks.
        """
        sum_s   = summary["sum"].add_prefix("sum_")
        mean_s  = summary["mean"].add_prefix("mean_")
        count_s = summary["count"].add_prefix("count_")
        raw = pd.concat([sum_s, mean_s, count_s]).to_dict()
        return {k: (int(v) if k.startswith("count_") else float(v)) for k, v in raw.items()}
        