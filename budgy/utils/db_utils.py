#!python3
"""
Contains functions for general database operations.

Module Overview:
===============
Functions:
----------
    - upload_all_csv_to_db(): Batch processes all CSV files in a directory, validates and uploads
        transaction records to the database. Skips files that have already been successfully uploaded.
    - upload_csv_to_db(): Converts and validates a single CSV file line by line, then uploads
        transactions to the database. Handles duplicates by updating category information if needed.
        Generates update entries to track upload status.
    - iter_val_csv_file(): Generator function that iterates through CSV file records, validates
        each against the schema, and generates unique hashes based on transaction content and
        occurrence count to detect duplicates.
    - update_categories_if_diff(): Checks for duplicate transactions by base hash and updates
        category information if categories differ between the new record and existing database records.
    - iter_csv_not_uploaded(): Generator function that yields CSV file paths from the specified
        directory that have not yet been successfully uploaded to the database.
    - generate_update_entry(): Creates or updates an entry in the updates table for a given CSV file.
        Raises DuplicateError if the file has already been completely uploaded.
    - validate_transaction(): Validates a single CSV record against the schema, performs type
        conversions on each column, and sets the status based on transaction amount.
    - generate_base_hash(): Generates a hash based on transaction content (authorized date, posted date,
        account name, description, and amount) to identify transactions with identical information.
    - parse_timestamp(): Parses timestamp strings in "%Y-%m-%d" format to datetime objects.
    - set_status_unchecked(): Sets transaction status to UNCHECKED if the amount is greater than zero,
        indicating it may need manual review for repayment or exclusion classification.
    - clear_tables(): Clears all records from both the transactions and updates tables with optional
        user confirmation prompt or force flag.

Dependencies:
- budgy.utils.db_models: Provides ORM table definitions, database managers, Column namedtuple,
    and the columns mapping list.
- local_db: Custom ORM module providing DatabaseManager and DuplicateError.
- budgy.utils.file_utils: Provides EDirectories enum, LoggingExtras class, and get_csv_filenames() function.
    budgy.utils.db_utils.py
"""
# Standard library imports
import csv
from collections import defaultdict
from datetime import datetime
import hashlib
import os
from typing import Dict, Generator, List

# Import database management classes from local_db module
from local_db import DatabaseManager, DuplicateError

# Local imports
from budgy.utils.file_utils import EDirectories, LoggingExtras, get_csv_filenames
from budgy.utils.db_models import (
    TransactionsTable, UpdatesTable, TableStatus,
    transactions_table_manager, update_table_manager,
    Column, columns
)

# initialize module logger
import logging
logger = logging.getLogger(__name__)



# NOTE: We should be checking the updates BEFORE we actually want to generate a new entry! make check for filepath function.

def generate_update_entry(filepath: str, status: TableStatus, updates_db_manager: DatabaseManager=update_table_manager):
    """
    Creates an update entry for the update table and handles potential errors.

    Args:
        filepath (str): the filepath being uploaded to the transactions database
        status (UpdatesTableStatus): The status to register the update with
        update_table_manager (DatabaseManager): The table that the update is being pushed to (changed for testing)
    """
    matching_items = updates_db_manager.fetch_items_by_attribute(filepath=filepath)

    if matching_items:
        if matching_items[0].status == TableStatus.COMPLETE:
            logger.error(f"File {filepath} already exists in {updates_db_manager.table_name}", extra={LoggingExtras.FILE: filepath})
            raise DuplicateError(filepath, UpdatesTable, message="Entry for filepath already exists in:")

        else:
            updates_db_manager.update_item(matching_items[0].id, status=status)

    else:
        updates_db_manager.add_item(
            timestamp=datetime.now(),
            filepath=filepath,
            status=status
        )


# Check whether or not the CSV data file has been uploaded to the database and return filename
def iter_csv_not_uploaded(csv_directory=EDirectories.CSV_DIR, updates_db_manager: DatabaseManager=update_table_manager) -> Generator:
    """Iterates through the CSV files in the csv_downlaods directory and checks whether or not they have been uploaded to the database."""

    # Iterate over CSV files in directory
    for filepath in get_csv_filenames(csv_directory=csv_directory):
        item = updates_db_manager.fetch_items_by_attribute(filepath=filepath)

        # If no item is returned, yield the file path.
        if not item:
            logger.info(f"CSV file {os.path.basename(filepath)} has not yet been uploaded to the database.", extra={LoggingExtras.FILE: filepath})
            yield filepath

        # If more than one value is returned, an error occured somewhere
        elif len(item) >= 2:
            filepath = item[0].filepath
            logger.error(f"Multiple items found with the same filepath, {filepath}", extra={LoggingExtras.FILE: filepath})
            raise DuplicateError(filepath, UpdatesTable)

        # If the returned item has it's status set to complete, do nothing
        elif item[0].status == TableStatus.COMPLETE:
            logger.info(f"CSV file {os.path.basename(filepath)} has already been uploaded to the database.", extra={LoggingExtras.FILE: filepath})

        # If the returned item's status is not set to complete, then field the filepath
        elif item[0].status != TableStatus.COMPLETE:
            logger.info(f"CSV file {os.path.basename(filepath)} has not yet been uploaded to the database.", extra={LoggingExtras.FILE: filepath})
            yield filepath

        # Raise an error for unhandled case
        else:
            logger.error("Unahndled case encountered during CSV upload check", extra={LoggingExtras.FILE: filepath})



def set_status_unchecked(record: dict) -> dict:
    """
    If the amount of the transaction is greater than zero (i.e. transfer or income),
    we may want to check and see if it is a repayment or needs to be excluded

    Args:
        record (dict): the record to check
    """
    if record[TransactionsTable.amount.name] > 0:
        record[TransactionsTable.status.name] = TableStatus.UNCHECKED
    return record


def validate_transaction(csv_record: Dict, columns: List[Column]):
    """Validates each record against the Schema to ensure that the data is correctly uploaded to the database."""
    db_record = {}
    for col in columns:
        value = csv_record[col.src].strip()
        db_record[col.dest] = col.convert(value)

    # Initialize repayment and exclude status to false for all transactions, we can update these later if needed
    db_record[TransactionsTable.repayment.name] = False
    db_record[TransactionsTable.exclude.name] = False

    return set_status_unchecked(db_record)


def generate_base_hash(record: dict) -> str:
    """
    Hash based purely on transaction content — no position.
    Uses authorized and posted date, account name, description, and amount to generate the hash.
    NOTE: Do not use primary or detailed category as those are subject to change in future!
    """
    unique_string = f"\
        {record[TransactionsTable.authorized_date.name]}:\
        {record[TransactionsTable.posted_date.name]}:\
        {record[TransactionsTable.account_name.name]}:\
        {record[TransactionsTable.description.name]}:\
        {record[TransactionsTable.amount.name]}"
    return hashlib.sha256(unique_string.encode()).hexdigest()


# Iterate through the lines in the CSV and validate each line
def iter_val_csv_file(csv_filepath: str, columns: List[Column]) -> Generator:
    """
    Iterates through each line in the CSV file and provides them as a generator.
    Also validates each line against the schema and generates a unique hash based on the record information and number of occurances

    Args:
        csv_filepath (str): the filepath of the csv being uploaded
        columns (List[Column]): the column mapping and conversion information for the csv upload
    """
    logger.info(f"Iterating and validating CSV file: {os.path.basename(csv_filepath)}", extra={LoggingExtras.FILE: csv_filepath})

    # First pass: count total occurrences of each base hash
    occurrence_counter = defaultdict(int)

    with open(csv_filepath, mode="r", encoding="utf-8") as f:
        transactions = csv.DictReader(f)

        for csv_record in transactions:
            db_record = validate_transaction(csv_record, columns)

            # Generate a unique hash for each transaction record based on the info and occurance count
            base_hash = generate_base_hash(db_record)
            count = occurrence_counter[base_hash]  # 0-indexed: first occurrence = 0
            final_hash = hashlib.sha256(f"{base_hash}:{count}".encode()).hexdigest()
            occurrence_counter[base_hash] += 1
            db_record["base_hash"] = base_hash
            db_record["uq_hash"] = final_hash

            yield db_record


# If a duplicate is detected in the database, we want to check and make sure the categories are up to date
def update_categories_if_diff(record: dict, transactions_db_manager: DatabaseManager=transactions_table_manager):
    """
    If a duplicate transaction is detected based on the base hash, we want to check and make sure the categories are up to date.
    This is because categories can be updated later on and we want to make sure the database holds the most up to date cateogry information.

    Args:
        record (dict): the record to check for duplicates and update categories for
        transactions_db_manager (DatabaseManager): the database manager for the transactions table (changed for testing
    """
    logger.debug(f"Checking for cagegory different between duplicates based on base hash: {record[TransactionsTable.base_hash.name]}")
    logger.debug(f"Updating primary and detailed categories for base hash: {record[TransactionsTable.base_hash.name]}")

    db_records = transactions_db_manager.fetch_items_by_attribute(base_hash=record[TransactionsTable.base_hash.name])
    base_hash = record[TransactionsTable.base_hash.name]

    for db_record in db_records:
        # If the detailed category matches, then the primary category must also be the same, pass.
        if record[TransactionsTable.detailed_category.name] == db_record.detailed_category:
            logger.debug(f"Categories are the same for record with base hash: {base_hash}. No update needed.", extra={LoggingExtras.BASE_HASH: base_hash})
            continue

        # Update the existing record or record with the new cateogry informaiton from the csv file if the categories don't match
        else:
            try:
                transactions_db_manager.update_item(
                    item_id=db_record.id,
                    primary_category=record[TransactionsTable.primary_category.name],
                    detailed_category=record[TransactionsTable.detailed_category.name]
                )
            except Exception as e:
                logger.exception(f"Exception encountered during category update for base hash: {base_hash}", extra={LoggingExtras.BASE_HASH: base_hash})
                raise e


# Insert data into database, checking to make sure it is not a duplicate
def upload_csv_to_db(
        csv_filepath: str,
        columns: List[Column]=columns,
        transactions_db_manager: DatabaseManager=transactions_table_manager,
        updates_db_manager: DatabaseManager=update_table_manager
    ):
    """
    Converts and validates the new transactions line by line then uploads to the transactions database.
    Returns whether or not the file was uploaded successfully.
    Also enforces that no csv can be uploaded if it already has a posted upload with completed status.

    Args:
        csv_filepath (str): the filepath of the csv being uploaded
        columns (List[Column]): the column mapping and conversion information for the csv upload
        record_db_manager (DatabaseManager): the database manager for the transactions table (changed for testing)
        update_table_manager (DatabaseManager): the database manager for the updates table
    """
    logger.info(f"Beginning upload of CSV file to database: {os.path.basename(csv_filepath)}", extra={LoggingExtras.FILE: csv_filepath})
    logger.performance(f"Beginning csv upload process for {csv_filepath}", process_id=LoggingExtras.UPLOAD)

    transactions_original_state = transactions_db_manager.to_dataframe()

    for record in iter_val_csv_file(csv_filepath, columns):

        # Check to see if the base hash name of the transaction is already in the transactions table
        if record[TransactionsTable.base_hash.name] in transactions_original_state[TransactionsTable.base_hash.name].values:
            # if it is, update the catgories if they are different.
            update_categories_if_diff(record, transactions_db_manager=transactions_db_manager)

        else:
            try:
                transactions_db_manager.add_item(**record)

            # Gracefully handle duplicate errors, thank you program for detecting duplicates
            except DuplicateError as e:
                pass

            # Unhandled exceptions should be logged so we can keep track of whether or not the upload was complete
            except Exception as e:
                logger.exception(f"Exception encountered during data upload to {transactions_db_manager}", extra={LoggingExtras.RECORD: record})
                generate_update_entry(
                    csv_filepath,
                    TableStatus.INCOMPLETE,
                    updates_db_manager=updates_db_manager
                )
                raise e

    # Generate an update entry for the file uploaded with the status of complete if no errors were encountered
    logger.info(f"Completed upload of CSV file to database: {os.path.basename(csv_filepath)}", extra={LoggingExtras.FILE: csv_filepath})
    generate_update_entry(
        csv_filepath,
        TableStatus.COMPLETE,
        updates_db_manager=updates_db_manager
    )

    logger.performance(f"Completed csv upload process for {csv_filepath}", process_id=LoggingExtras.UPLOAD)


def upload_all_csv_to_db(
        columns: List[Column]=columns,
        transactions_db_manager: DatabaseManager=transactions_table_manager,
        updates_db_manager: DatabaseManager=update_table_manager,
        csv_dir: str=EDirectories.CSV_DIR
    ):
    """
    Iterates through all csv files in csv_dir.
    Converts and validates the new transactions line by line then uploads to the transactions database.
    Returns whether or not the file was uploaded successfully.
    Also enforces that no csv can be uploaded if it already has a posted upload with completed status.

    Args:
        columns (List[Column]): the column mapping and conversion information for the csv upload
        record_db_manager (DatabaseManager): the database manager for the transactions table (changed for testing)
        update_table_manager (DatabaseManager): the database manager for the updates table
        csv_dir (str): path to the direcotry where the function should search for csv files to upload
    """
    logger.info(f"Beggining upload of all csv files in {EDirectories.CSV_DIR} to {transactions_db_manager.table_name}")
    failed_files = []

    for csv_filepath in iter_csv_not_uploaded(csv_directory=csv_dir, updates_db_manager=updates_db_manager):
        try:
            upload_csv_to_db(
                csv_filepath,
                columns=columns,
                transactions_db_manager=transactions_db_manager,
                updates_db_manager=updates_db_manager
            )

        except Exception as e:
            logger.warning(f"Failed to upload {csv_filepath} to {transactions_db_manager.table_name}", extra={LoggingExtras.FILE: csv_filepath})
            failed_files.append(csv_filepath)

    if failed_files:
        logger.warning(f"Batch upload completed with {len(failed_files)} files failed")
    else:
        logger.info(f"New CSV file upload complete.")


def clear_tables(force: bool=False):
    logger.warning(f"Database table clearing initiated. force: {force}")
    if not force:
        answer = input("Are you sure you would like to clear the database tables? (Y/n)")
        if answer == "Y":
            logger.info(f"Database table clearing accepted. Clearing database tables.")
            transactions_table_manager.clear_table()
            update_table_manager.clear_table()

        elif answer == "n":
            logger.info(f"Database table clearing rejected. Aborting.")

    else:
        transactions_table_manager.clear_table()
        update_table_manager.clear_table()
