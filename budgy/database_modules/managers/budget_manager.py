#!python3
"""
budgy.database_modules.managers.budget_manager.py -
Module containing the class-based manager for the budgets table.

Classes:
    - BudgetsTableManager: DatabaseManager subclass for the BudgetsTable.

Variables:
    - budgets_manager: Module-level BudgetsTableManager instance.
"""
# Standard library imports

# Third party imports

# Custom imports
from pleasant_database import DatabaseFile, DatabaseManager

# Local imports
from budgy.database_modules.managers.common import DB_FILE
from budgy.database_modules.models.budgets import BudgetsTable

# initialize module logger
import logging
logger = logging.getLogger(__name__)


class BudgetsTableManager(DatabaseManager):
    """Manager for the budgets table."""

    def __init__(self, db_file: DatabaseFile):
        super().__init__(BudgetsTable, db_file)

    
    def upload_budget(budget: dict) -> None:
        """Verifies budget values and uploads to database table"""
        pass

    # def _create_entry_hash(self) -> :
    #     """return"""
    #     unique_string = f"\
    #     {record[BudgetsTable..name]}:\
    #     {record[BudgetsTable..name]}:\
    #     {record[BudgetsTable..name]}:\
    #     {record[BudgetsTable..name]}:\
    #     {record[BudgetsTable..name]}"
    #     return hashlib.sha256(unique_string.encode()).hexdigest()
        


# Module-level instance for production use
budgets_manager = BudgetsTableManager(DB_FILE)
