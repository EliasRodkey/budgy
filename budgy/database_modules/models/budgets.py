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
from local_db import BaseTable, ESQLDataTypes

# Local imports
from .common import Column, parse_date

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

    id = ESQLDataTypes.Column(ESQLDataTypes.Integer, primary_key=True, autoincrement=True)
    date_created = ESQLDataTypes.Column(ESQLDataTypes.DateTime)
    income = ESQLDataTypes.Column(ESQLDataTypes.Float)
    transfers = ESQLDataTypes.Column(ESQLDataTypes.Float)
    debt_payments = ESQLDataTypes.Column(ESQLDataTypes.Float)
    investments = ESQLDataTypes.Column(ESQLDataTypes.Float)
    bank_fees = ESQLDataTypes.Column(ESQLDataTypes.Float)
    food_and_drink = ESQLDataTypes.Column(ESQLDataTypes.Float)
    shopping = ESQLDataTypes.Column(ESQLDataTypes.Float)
    housing_and_utilities = ESQLDataTypes.Column(ESQLDataTypes.Float)
    health_and_wellness = ESQLDataTypes.Column(ESQLDataTypes.Float)
    entertainment = ESQLDataTypes.Column(ESQLDataTypes.Float)
    insurance = ESQLDataTypes.Column(ESQLDataTypes.Float)
    services = ESQLDataTypes.Column(ESQLDataTypes.Float)
    transportation = ESQLDataTypes.Column(ESQLDataTypes.Float)
    travel = ESQLDataTypes.Column(ESQLDataTypes.Float)
    government_and_charity = ESQLDataTypes.Column(ESQLDataTypes.Float)
    other = ESQLDataTypes.Column(ESQLDataTypes.Float)



budget_columns = [
    Column()
]