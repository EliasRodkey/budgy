#!python3
"""
budgy.database_modules.models.summaries.py -
Contains ORM table definitions, database managers, and CSV column mappings for budgy summaries db table.

Classes:
    - SummariesTable: ORM class representing the summaries table in the database.

Variables:
    - summary_columns: List of Column namedtuples mapping CSV headers to TransactionsTable columns
        with type conversion functions for transaction data import.
"""
# Standard library imports

# Custom imports
# TODO: Add ForeignKey to local_db import ESQLDataTypes
from sqlalchemy import ForeignKey, UniqueConstraint, Column, Float, Integer, DateTime
from pleasant_database import BaseTable

# Local imports
from .common import Field

# initialize module logger
import logging
logger = logging.getLogger(__name__)



class SummariesTable(BaseTable):
    """
    Class representing the summaries table in the database.
    This table stores all the summary spending data calculated from the transactions database.

    Database Structure:
        table name: summaries
    Columns:
        - id: primary key, autoincremented. unique per row
        - date: DateTime
        - month: integer (1-12)
        - year: integer
        - budget_id: integer, tied to budgets table
        - PrimaryCateogry category names using as_snake_case_headers method
        - DetailedCateogry category names using as_snake_case_headers method
    """

    __tablename__ = "summaries"

    # TODO: Add UniqueConstraint to ESQLDataTypes in local_db, or maybe remove all together and just import from sqlalchemy?
    # Enforce unique combination across (user_id, project_id)
    __table_args__ = (
        UniqueConstraint('month', 'year', name='month_of_summary'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime)
    month = Column(Integer)
    year = Column(Integer)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=False)
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
    wages = Column(Float)
    dividends = Column(Float)
    interest = Column(Float)
    benefits_and_pension = Column(Float)
    tax_refunds = Column(Float)
    unemployment = Column(Float)
    other_income = Column(Float)
    account_transfers = Column(Float)
    investment_transfers = Column(Float)
    savings_transfers = Column(Float)
    cash_deposits = Column(Float)
    cash_withdrawals = Column(Float)
    loans_and_cash_advances = Column(Float)
    person_to_person_payments = Column(Float)
    other_transfers = Column(Float)
    credit_card_payments = Column(Float)
    auto_loan_payments = Column(Float)
    student_loan_payments = Column(Float)
    personal_loan_payments = Column(Float)
    other_debt_payments = Column(Float)
    buy = Column(Float)
    sell = Column(Float)
    atm_fees = Column(Float)
    foreign_transaction_fees = Column(Float)
    insufficient_funds = Column(Float)
    interest_charge = Column(Float)
    late_fees = Column(Float)
    wire_fees = Column(Float)
    overdraft_fees = Column(Float)
    other_bank_fees = Column(Float)
    restaurants_and_bars = Column(Float)
    groceries = Column(Float)
    coffee_shops = Column(Float)
    liquor_stores = Column(Float)
    other_food_and_drink = Column(Float)
    clothing_and_accessories = Column(Float)
    electronics = Column(Float)
    pet_supplies = Column(Float)
    gifts = Column(Float)
    office_supplies = Column(Float)
    sports_and_outdoors = Column(Float)
    retail = Column(Float)
    convenience_stores = Column(Float)
    hair_and_beauty = Column(Float)
    tabacco_and_vape = Column(Float)
    other_shopping = Column(Float)
    rent = Column(Float)
    mortgage_payments = Column(Float)
    home_improvement_and_repairs = Column(Float)
    phone_and_internet = Column(Float)
    gas_and_electricity = Column(Float)
    water_sewer_and_garbage = Column(Float)
    security = Column(Float)
    hoa_fee = Column(Float)
    property_tax = Column(Float)
    other_housing_and_utilities = Column(Float)
    medical = Column(Float)
    pharmacy = Column(Float)
    dental = Column(Float)
    vision = Column(Float)
    nursing = Column(Float)
    fitness = Column(Float)
    personal_care = Column(Float)
    other_health_and_wellness = Column(Float)
    gambling = Column(Float)
    books_and_news = Column(Float)
    movies_and_tv = Column(Float)
    music_and_audio = Column(Float)
    games = Column(Float)
    events_and_recreation = Column(Float)
    other_entertainment = Column(Float)
    life_insurance = Column(Float)
    health_insurance = Column(Float)
    auto_insurance = Column(Float)
    home_insurance = Column(Float)
    other_insurance = Column(Float)
    household_services = Column(Float)
    education_services = Column(Float)
    veterinary_services = Column(Float)
    childcare_services = Column(Float)
    digital_services = Column(Float)
    legal_services = Column(Float)
    financial_services = Column(Float)
    shipping = Column(Float)
    moving_and_storage = Column(Float)
    other_services = Column(Float)
    gas_and_ev_charging = Column(Float)
    car_services = Column(Float)
    public_transit = Column(Float)
    taxi_and_ride_shares = Column(Float)
    parking_and_tolls = Column(Float)
    other_transportation = Column(Float)
    flights = Column(Float)
    hotels = Column(Float)
    rental_cars = Column(Float)
    other_travel = Column(Float)
    tax_payments = Column(Float)
    government_fees = Column(Float)
    charity = Column(Float)
    other_government_and_charity = Column(Float)



summary_columns = [
    Field(column_name, column_name, column_type)
    for column_name, column_type in SummariesTable.get_column_python_types().items()
    if column_name != SummariesTable.id.name
]