#!python3
"""
backend.database_modules.managers.budget_assignments_manager
Manager for the budget_assignments table.
"""
from pleasant_database import DatabaseFile, DatabaseManager

from backend.database_modules.models.budget_assignments import BudgetAssignmentsTable

from pleasant_loggers import get_logger
logger = get_logger(__name__)


class BudgetAssignmentsManager(DatabaseManager):

    def __init__(self, db_file: DatabaseFile):
        super().__init__(BudgetAssignmentsTable, db_file)

    def get_all(self) -> list:
        return self.fetch_all_items()

    def get_effective_assignment(self, month: str):
        """Return the assignment with the most recent effective_from <= month, or None."""
        all_assignments = self.fetch_all_items()
        eligible = [a for a in all_assignments if a.effective_from <= month]
        if not eligible:
            return None
        return max(eligible, key=lambda a: a.effective_from)
