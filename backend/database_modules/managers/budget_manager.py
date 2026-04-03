#!python3
"""
budgy.database_modules.managers.budget_manager.py -
Module containing the class-based manager for the budgets table.

Classes:
    - BudgetsTableManager: DatabaseManager subclass for the BudgetsTable.
"""
# Standard library imports
from datetime import datetime
import hashlib

# Custom imports
from pleasant_database import DatabaseIntegrityError, DatabaseFile, DatabaseManager, ItemNotFoundError

# Local imports
from backend.database_modules.managers.common import DB_FILE, DuplicateError
from backend.database_modules.models.budgets import BudgetsTable, budget_columns
from backend.utils.analysis_utils import PrimaryCategories
from backend.utils.file_utils import LoggingExtras

# initialize module logger
import logging
logger = logging.getLogger(__name__)


class BudgetsTableManager(DatabaseManager):
    """
    Manager for the budgets table.
    Budgets should be uploaded on a "per month" spending basis.

    Methods:
        - upload_budgte: Verifies budget values and uploads to database table.
        - fetch_budget_by_id: Retrieves a budget from the budgets table with the given budget_id.
        - calculate_net_gain_or_loss: Calculates the total expected gain or loss from a given budget
    """

    def __init__(self, db_file: DatabaseFile):
        super().__init__(BudgetsTable, db_file)

    
    def upload_budget(self, budget: dict) -> None:
        """Verifies budget values and uploads to database table, budget should be a dict with one item for each PrimaryCategories enum value as header."""
        logger.info(f"Uploading budget to {self.table_name}...")

        if BudgetsTable.date_created.name not in budget.keys():
            date_created = datetime.now()

        else:
            date_created = budget.pop(BudgetsTable.date_created.name)
            assert isinstance(date_created, datetime)

        clean_budget = self._clean_budget(budget)
        uq_hash = self._create_uq_hash(clean_budget)

        if self._uq_hash_exists(uq_hash):
            raise DuplicateError(uq_hash, self.table_name)
        
        clean_budget[BudgetsTable.uq_hash.name] = uq_hash
        clean_budget[BudgetsTable.net_gain_or_loss.name] = self.calculate_net_gain_or_loss(clean_budget)
        clean_budget[BudgetsTable.date_created.name] = date_created

        try:
            self.add_item(**clean_budget)
            logger.info(f"Successfully uploaded budget to {self.table_name}")

        except DatabaseIntegrityError:
            logger.exception(f"Budget already exists in budgets table, skipping upload.")
            return
        
        except Exception as e:
            logger.error(f"Unknown exception occured during budget upload: {e}")
            raise e


    def fetch_budget_by_id(self, budget_id: int) -> BudgetsTable:
        """Retrieves a budget from the budgets table with the given budget_id."""
        logger.info(f"Retrieving budget {budget_id} from {self.table_name}")

        try:
            return self.fetch_item_by_id(budget_id)
        
        except ItemNotFoundError:
            logger.warning(f"No budget exists with ID {budget_id}")
            return BudgetsTable
        
        except Exception as e:
            logger.error(f"Unknown exception occured retrieving budget {budget_id}: {e}")
            raise
    

    def calculate_net_gain_or_loss(self, budget_record: dict) -> float:
        """Calculates the total expected gain or loss from a given budget."""
        logger.info(f"Calculating net gain or loss for budget: {budget_record[BudgetsTable.uq_hash.name]}")

        # Income is just the income category
        total_income = budget_record[BudgetsTable.income.name]

        # Spending is everything else (remove income)
        spending_categories = PrimaryCategories.as_snake_case_headers()
        spending_categories.remove(BudgetsTable.income.name)
        total_spending = sum([budget_record[category] for category in spending_categories])

        return total_income - total_spending
    

    def _clean_budget(self, budget_record: dict) -> dict:
        """Checks types and names of budget_record to make sure it is ready for upload."""
        logger.debug(f"Verifying budget...")

        primary_categories = PrimaryCategories.as_snake_case_headers()
        for category in primary_categories:
            if category not in budget_record.keys():
                budget_record[category] = 0.0
            else:
                assert isinstance(budget_record[category], float)
        
        for field in budget_record.keys():
            if field not in BudgetsTable.get_column_names():
                raise ValueError(f"Budget entry not valid: {field}")
        
        assert len(budget_record) == len(primary_categories)
        return budget_record
        
    
    def _create_uq_hash(self, budget_record: dict) -> str:
        """Creates a unique hash for the budget based on the values provided in each category."""
        unique_str = ""
        for category in PrimaryCategories.as_snake_case_headers():
            unique_str += str(round(budget_record[category], 2))

        return hashlib.sha256(unique_str.encode()).hexdigest()
    

    def _budget_exists_by_id(self, budget_id: int) -> bool:
        """Checks to see if a given budget_id already exists in the budgets table."""
        logger.debug(f"Checking if budget ID {budget_id} alredy exists")

        try:
            self.fetch_item_by_id(budget_id)
            return True
        
        except ItemNotFoundError:
            return False


    def _uq_hash_exists(self, uq_hash: str) -> bool:
        """Checks to see if the given hash already exists in the budgets table."""
        logger.debug(f"Checking if budget hash {uq_hash} already exists", extra={LoggingExtras.UQ_HASH: uq_hash})

        return_item = self.fetch_items_by_attribute(uq_hash=uq_hash)
        return bool(return_item)
