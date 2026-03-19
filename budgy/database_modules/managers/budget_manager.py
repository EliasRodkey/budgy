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
from local_db import DatabaseFile, DatabaseManager

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


# Module-level instance for production use
budgets_manager = BudgetsTableManager(DB_FILE)
