#!python3
"""
budgy.database_modules.models.budgets.py -
Contains ORM table definitions, database managers, and CSV column mappings for budgy budgets db table.

Classes:
    - BudgetsTable: ORM class representing the budgets table in the database.

Variables:
    - budget_columns: List of Column namedtuples mapping CSV headers to TransactionsTable columns
        with type conversion functions for transaction data import.
"""
# Standard library imports

# Custom importss
from sqlalchemy import Column, Integer, DateTime, Float, String
from pleasant_database import BaseTable

# Local imports
from .common import Field, parse_date

# initialize module logger
import logging
logger = logging.getLogger(__name__)



class BudgetsTable(BaseTable):
    """
    Class representing the budgets table in the database.
    This table stores all the different budget configurations.

    Database Structure:
        table name: budgets
    Columns:
        - id: primary key, autoincremented. unique per row
        - date_created: DateTime
        - budget_id: integer, tied to budgets table
        - PrimaryCateogry category names using as_snake_case_headers method
    """

    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date_created = Column(DateTime)
    income = Column(Float)
    transfers = Column(Float)
    debt_payments = Column(Float)
    investments = Column(Float)
    bank_fees = Column(Float)
    food_and_drink = Column(Float)
    shopping = Column(Float)
    housing_and_utilities = Column(Float)
    health_and_wellness = Column(Float)
    entertainment = Column(Float)
    insurance = Column(Float)
    services = Column(Float)
    transportation = Column(Float)
    travel = Column(Float)
    government_and_charity = Column(Float)
    other = Column(Float)
    uq_hash = Column(String, unique=True)



budget_columns = [
    Field(column_name, column_name, type) for column_name, type in BudgetsTable.get_column_python_types().items()
]