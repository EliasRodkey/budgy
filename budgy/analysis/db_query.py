"""
"""

# Standard library imports
from typing import Dict, Generator, List

# Local imports
from budgy.utils.db_utils import DatabaseManager, BaseTable, transactions_table_manager
from budgy.utils.file_utils import LoggingExtras

# initialize module logger
import logging
logger = logging.getLogger(__name__)


def retrieve_records_by_primary_category(category: str, db_manager: DatabaseManager=transactions_table_manager) -> List[BaseTable]:
    """
    Retrieves all records from a given primary category from the database associated with the given Database Manager

    Args:
        category (str): The primary category to filter records by.
        db_manager (DatabaseManager, optional): The Database Manager instance to use for querying the database. Defaults to transactions_table_manager.
    """
    logger.debug(f"Retrieving records for primary category: {category} from database using manager: {db_manager}", extra={LoggingExtras.PRIMARY_CATEGORY: category})

    try:
        records = db_manager.fetch_items_by_attribute(primary_category=category)

    except Exception as e:
        logger.exception(f"Unhandled error retrieving records for category: {category}.")
        return []

    if not records:
        logger.warning(f"No records found for primary category: {category}")
    
    return records


def retrieve_records_by_detailed_category(category: str, db_manager: DatabaseManager=transactions_table_manager) -> List[BaseTable]:
    """
    Retrieves all records from a given detailed category from the database associated with the given Database Manager

    Args:
        category (str): The detailed category to filter records by.
        db_manager (DatabaseManager, optional): The Database Manager instance to use for querying the database. Defaults to transactions_table_manager.
    """
    logger.debug(f"Retrieving records for detailed category: {category} from database using manager: {db_manager}", extra={LoggingExtras.DETAILED_CATEGORY: category})

    try:
        records = db_manager.fetch_items_by_attribute(detailed_category=category)

    except Exception as e:
        logger.exception(f"Unhandled error retrieving records for category: {category}.")
        return []

    if not records:
        logger.warning(f"No records found for detailed category: {category}")
    
    return records
