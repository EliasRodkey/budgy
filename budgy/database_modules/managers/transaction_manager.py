#!python3
"""
budgy.database_modules.managers.transaction_manager.py -
Module containing class-based managers for the transactions and updates tables.

Classes:
    - TransactionsTableManager: DatabaseManager subclass for the TransactionsTable.
        Provides methods for querying and analyzing transaction records.
    - UpdatesTableManager: DatabaseManager subclass for the UpdatesTable.
        Provides methods for tracking CSV upload history.

Variables:
    - transactions_manager: Module-level TransactionsTableManager instance.
    - updates_manager: Module-level UpdatesTableManager instance.
"""
# Standard library imports
from datetime import datetime
from typing import Generator, List, Tuple
import os

# Third party imports
import pandas as pd

# Custom imports
from pleasant_database import DatabaseFile, DatabaseIntegrityError, DatabaseManager

# Local imports
from budgy.database_modules.managers.common import DuplicateError, convert_datetime_nums_to_range, format_column_names
from budgy.database_modules.models.common import Field, TableStatus
from budgy.database_modules.models.transactions import TransactionsTable, UpdatesTable, transaction_columns
from budgy.utils.analysis_utils import PrimaryCategories, DetailedCategories, CategoriesEnum
from budgy.utils.file_utils import EDirectories, LoggingExtras, get_csv_filenames
from budgy.database_modules.io.transactions_csv_loader import iter_val_csv_file

# initialize module logger
import logging
logger = logging.getLogger(__name__)



class UpdatesTableManager(DatabaseManager):
    """
    Manager for the transaction_updates table. Tracks CSV upload history.

    Methods:
        - generate_update_entry: Creates or updates an entry in the updates table for a given CSV filepath.
        - iter_csv_not_uploaded: Generator that yields CSV filepaths not yet successfully uploaded.
    """

    def __init__(self, db_file: DatabaseFile):
        super().__init__(UpdatesTable, db_file)


    def generate_update_entry(self, filepath: str, status: TableStatus) -> None:
        """
        Creates an update entry for the update table and handles potential errors.

        Args:
            filepath (str): the filepath being uploaded to the transactions database
            status (TableStatus): The status to register the update with
        """
        matching_items = self.fetch_items_by_attribute(filepath=filepath)

        if matching_items:
            if matching_items[0].status == TableStatus.COMPLETE:
                logger.error(f"File {filepath} already exists in {self.table_name}", extra={LoggingExtras.FILE: filepath})
                raise DuplicateError(filepath, UpdatesTable, message="Entry for filepath already exists in:")

            else:
                self.update_item(matching_items[0].id, status=status)

        else:
            self.add_item(
                timestamp=datetime.now(),
                filepath=filepath,
                status=status
            )

    def iter_csv_not_uploaded(self, csv_directory=EDirectories.CSV_DIR) -> Generator:
        """Iterates through the CSV files in the csv_downloads directory and checks whether or not they have been uploaded to the database."""

        for filepath in get_csv_filenames(csv_directory=csv_directory):
            item = self.fetch_items_by_attribute(filepath=filepath)

            # If no item is returned, yield the file path.
            if not item:
                logger.info(f"CSV file {os.path.basename(filepath)} has not yet been uploaded to the database.", extra={LoggingExtras.FILE: filepath})
                yield filepath

            # If more than one value is returned, an error occurred somewhere
            elif len(item) >= 2:
                filepath = item[0].filepath
                logger.error(f"Multiple items found with the same filepath, {filepath}", extra={LoggingExtras.FILE: filepath})
                raise DuplicateError(filepath, UpdatesTable)

            # If the returned item has its status set to complete, do nothing
            elif item[0].status == TableStatus.COMPLETE:
                logger.info(f"CSV file {os.path.basename(filepath)} has already been uploaded to the database.", extra={LoggingExtras.FILE: filepath})

            # If the returned item's status is not set to complete, then yield the filepath
            elif item[0].status != TableStatus.COMPLETE:
                logger.info(f"CSV file {os.path.basename(filepath)} has not yet been uploaded to the database.", extra={LoggingExtras.FILE: filepath})
                yield filepath

            # Raise an error for unhandled case
            else:
                logger.error("Unhandled case encountered during CSV upload check", extra={LoggingExtras.FILE: filepath})



class TransactionsTableManager(DatabaseManager):
    """
    Manager for the transactions table. Provides querying and analysis methods.

    Methods:
        - retrieve_records_by_attribute_over_period: Queries transactions by date range and optional attributes, returns a DataFrame.
        - generate_monthly_category_report: Summarizes total spending per category for a given month and year.
        - return_category_count: Returns the number of transactions for a given category over a period.
    """

    def __init__(self, db_file: DatabaseFile, updates_manager: UpdatesTableManager):
        super().__init__(TransactionsTable, db_file)
        self.updates_manager = updates_manager


    def upload_csv(
            self,
            csv_filepath: str,
            columns: List[Field] = transaction_columns,
        ) -> List[TransactionsTable]:
        """
        Converts and validates the new transactions line by line then uploads to the transactions database.
        Also enforces that no csv can be uploaded if it already has a posted upload with completed status.

        Args:
            csv_filepath (str): the filepath of the csv being uploaded
            columns (List[Field]): the column mapping and conversion information for the csv upload
        
        Returns:
            List[TransactionTable]: A list of ORM objects that had their categories updated during the upload 
        """

        logger.info(f"Beginning upload of CSV file to database: {os.path.basename(csv_filepath)}", extra={LoggingExtras.FILE: csv_filepath})
        logger.performance(f"Beginning csv upload process for {csv_filepath}", process_id=LoggingExtras.UPLOAD)

        transactions_original_state = self.to_dataframe()

        updated_records = []
        for record in iter_val_csv_file(csv_filepath, columns):

            if record[TransactionsTable.base_hash.name] in transactions_original_state[TransactionsTable.base_hash.name].values:
                updated_records.extend(self._update_categories_if_diff(record))
                # TODO Compile update month / year pairs if applicable, make sure no duplicates, return to caller

            else:
                try:
                    self.add_item(**record)

                except DatabaseIntegrityError:
                    pass

                except Exception as e:
                    logger.exception(f"Exception encountered during data upload to {self}", extra={LoggingExtras.RECORD: record})
                    self.updates_manager.generate_update_entry(csv_filepath, TableStatus.INCOMPLETE)
                    raise e
        
        return updated_records

        logger.info(f"Completed upload of CSV file to database: {os.path.basename(csv_filepath)}", extra={LoggingExtras.FILE: csv_filepath})
        self.updates_manager.generate_update_entry(csv_filepath, TableStatus.COMPLETE)
        logger.performance(f"Completed csv upload process for {csv_filepath}", process_id=LoggingExtras.UPLOAD)


    def upload_all_csvs(
            self,
            columns: List[Field] = transaction_columns,
            csv_dir: str = EDirectories.CSV_DIR
        ) -> List[TransactionsTable]:
        """
        Iterates through all csv files in csv_dir and uploads only those not yet successfully uploaded.

        Args:
            columns (List[Field]): the column mapping and conversion information for the csv upload
            csv_dir (str): path to the directory where the function should search for csv files to upload
        
        Returns:
            List[TransactionTable]: A list of ORM objects that had their categories updated during the upload 
        """

        logger.info(f"Beginning upload of all csv files in {csv_dir} to {self.table_name}")
        failed_files = []
        updated_records = []

        for csv_filepath in self.updates_manager.iter_csv_not_uploaded(csv_directory=csv_dir):
            try:
                updated_records.extend(self.upload_csv(csv_filepath, columns=columns))

            except Exception:
                logger.warning(f"Failed to upload {csv_filepath} to {self.table_name}", extra={LoggingExtras.FILE: csv_filepath})
                failed_files.append(csv_filepath)

        if failed_files:
            logger.warning(f"Batch upload completed with {len(failed_files)} files failed")

        else:
            logger.info(f"New CSV file upload complete.")

        return updated_records


    def fetch_records_by_attribute_over_period(self, month: int=None, year: int=None, **kwargs) -> pd.DataFrame:
        """
        Retrieves all records from the transactions table that match the specified attributes
        and fall within the specified date range. Excludes transactions marked as excluded.

        Args:
            month (int): The month as an integer (1-12).
            year (int): The year as an integer (e.g., 2024).
            **kwargs: Arbitrary keyword arguments representing the attributes to filter by
                (e.g., primary_category='Food', detailed_category='Groceries').

        Returns:
            pd.DataFrame: A DataFrame of matching records.
        """
        start_date, end_date = convert_datetime_nums_to_range(month, year)

        logger.debug(
            f"Retrieving records from {start_date} to {end_date} with attributes: {kwargs} using manager: {self}",
            extra={
                LoggingExtras.START_DATE.value: start_date.strftime(LoggingExtras.DATETIME_FORMAT),
                LoggingExtras.END_DATE.value: end_date.strftime(LoggingExtras.DATETIME_FORMAT),
                LoggingExtras.ATTRIBUTES.value: kwargs
            }
        )

        attributes = {k: ("==", v) for k, v in kwargs.items()}
        attributes[TransactionsTable.authorized_date.name] = [(">=", start_date), ("<=", end_date)]
        attributes[TransactionsTable.exclude.name] = ("==", False)

        try:
            records = self.filter_items(attributes)

        except Exception as e:
            logger.exception(f"Unhandled error retrieving records for attributes: {attributes} over period: {start_date} to {end_date}")
            return pd.DataFrame()

        if not records:
            logger.warning(f"No records found over period with specified attributes: {start_date} to {end_date}.", extra={LoggingExtras.ATTRIBUTES: attributes})

        return self.convert_orm_list_to_dataframe(records)


    def retrieve_month_year_pairs(self) -> List[Tuple]:
        """Retrieves all of the month / year pairs in the database and returns them as a list of tuples [(month, year)]"""
        # TODO: Add __repr__ and __str__ methods to DatabaseManager class (duh)
        logger.info(f"Retrieving month year pairs from {self.table_name}")

        transactions_df = self.to_dataframe()

        if transactions_df.empty:
            logger.warning(f"No transactions present in {self.table_name}, no month / year pairs found.")
            return []

        grouped_df = transactions_df.groupby(
            transactions_df[TransactionsTable.authorized_date.name].dt.to_period("M")
        )[TransactionsTable.amount.name].sum()

        pairs = []
        for date in grouped_df.index:
            pairs.append((date.month, date.year))
        
        return pairs


    def generate_monthly_category_report(self, month: int, year: int) -> pd.DataFrame:
        """
        Generates a monthly category report for the specified month and year,
        summarizing the total amount spent in each category.
        Theoretically can return a whole year or all time reports by leaving month or year as None.
        See convert_datetime_nums_to_range.

        Args:
            month (int): The month as an integer (1-12).
            year (int): The year as an integer (e.g., 2024).

        Returns:
            pd.DataFrame: A DataFrame containing the total amount spent in each category. Or empty if no items found
        """
        logger.info(f"Generating monthly category report for month/year: {month}/{year} using manager: {self}.")

        records_df = self.fetch_records_by_attribute_over_period(month, year)
        columns = PrimaryCategories.as_snake_case_headers() + DetailedCategories.as_snake_case_headers()

        if records_df.empty:
            logger.info(f"No transactions found for month/year: {month}/{year}. Returning empty report.")
            return pd.DataFrame()
        
        try:
            primary_category_report = records_df.groupby(TransactionsTable.primary_category.name)[TransactionsTable.amount.name].sum().reset_index()
            detailed_category_report = records_df.groupby(TransactionsTable.detailed_category.name)[TransactionsTable.amount.name].sum().reset_index()

            primary_category_report.columns = ["category", "total"]
            detailed_category_report.columns = ["category", "total"]

            category_report = pd.concat([primary_category_report, detailed_category_report], axis=0).reset_index()

            category_report.category = format_column_names(category_report.category)
            category_report.set_index("category", inplace=True)

            category_report = category_report.T
            category_report.drop(index="index", inplace=True)

        except Exception as e:
            logger.exception(f"Error encountered while summarizing transactions from {month} / {year}: {e}")
            raise e

        return category_report


    def return_category_count(self, category: CategoriesEnum, month: int=None, year: int=None) -> int:
        """
        Returns an integer representing the number of transactions from the given category over a period of time.

        Args:
            category (CategoriesEnum): The category to count
            month (int): integer between 1-12 representing the month to search
            year (int): integer representing the year to search
        """
        if category in PrimaryCategories:
            records_df = self.fetch_records_by_attribute_over_period(month, year, primary_category=category.value)

        elif category in DetailedCategories:
            records_df = self.fetch_records_by_attribute_over_period(month, year, detailed_category=category.value)

        else:
            logger.error(f"The category {category} was not found in either PrimaryCategories or DetailedCategories", extra={LoggingExtras.CATEGORY: category.value})
            raise KeyError(f"The category {category} was not found in either PrimaryCategories or DetailedCategories")

        logger.info(f"Counting number of transactions for {category}")
        return records_df.shape[0]
    

    def _update_categories_if_diff(self, record: dict) -> List[TransactionsTable]:
        """
        If a duplicate transaction is detected based on the base hash, check and update categories
        if they differ from the existing database record.

        Args:
            record (dict): the record to check for duplicates and update categories for
        
        Returns:
            List[TransactionTable]: a list of the records updated
        """
        base_hash = record[TransactionsTable.base_hash.name]
        logger.debug(f"Checking for category difference between duplicates based on base hash: {base_hash}")

        db_records = self.fetch_items_by_attribute(base_hash=base_hash)
        updated_records = []
        for db_record in db_records:
            if record[TransactionsTable.detailed_category.name] == db_record.detailed_category:
                logger.debug(f"Categories are the same for record with base hash: {base_hash}. No update needed.", extra={LoggingExtras.BASE_HASH: base_hash})
                continue
            else:
                try:
                    self.update_item(
                        item_id=db_record.id,
                        primary_category=record[TransactionsTable.primary_category.name],
                        detailed_category=record[TransactionsTable.detailed_category.name]
                    )
                    updated_records.append(db_record)
                except Exception as e:
                    logger.exception(f"Exception encountered during category update for base hash: {base_hash}", extra={LoggingExtras.BASE_HASH: base_hash})
                    raise e

        return updated_records