#!python3
"""
backend.database_modules.models.budget_assignments
ORM table definition for the budget_assignments table.
"""
from sqlalchemy import Column, Integer, String, UniqueConstraint
from pleasant_database import BaseTable

from pleasant_loggers import get_logger
logger = get_logger(__name__)


class BudgetAssignmentsTable(BaseTable):
    """
    Records which budget is active from a given month onwards.
    The effective budget for any month M is the assignment with the most recent
    effective_from that is <= M.
    """

    __tablename__ = "budget_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    budget_id = Column(Integer)
    effective_from = Column(String)   # YYYY-MM
    note = Column(String, nullable=True)

    __table_args__ = (UniqueConstraint("effective_from"),)
