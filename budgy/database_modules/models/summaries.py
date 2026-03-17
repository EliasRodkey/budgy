#!python3
"""
"""
# Standard library imports

# Custom imports
from local_db import BaseTable, ESQLDataTypes

# Local imports
from .common import Column, parse_date

# initialize module logger
import logging
logger = logging.getLogger(__name__)



class SummaryTable(BaseTable):
    """
    Class representing the Summaries table in the database.
    This table stores all the summary spending data calculated from the transactions database.

    Database Structure:
        table name: transactions
    Columns:
    - 
    """

    __tablename__ = "summaries"

    id = ESQLDataTypes.Column(ESQLDataTypes.Integer, primary_key=True, autoincrement=True)
    date = ESQLDataTypes.Column(ESQLDataTypes.DateTime)
    month = ESQLDataTypes.Column(ESQLDataTypes.Integer)
    year = ESQLDataTypes.Column(ESQLDataTypes.Interval)
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
    wages = ESQLDataTypes.Column(ESQLDataTypes.Float)
    dividends = ESQLDataTypes.Column(ESQLDataTypes.Float)
    interest = ESQLDataTypes.Column(ESQLDataTypes.Float)
    benefits_and_pension = ESQLDataTypes.Column(ESQLDataTypes.Float)
    tax_refunds = ESQLDataTypes.Column(ESQLDataTypes.Float)
    unemployment = ESQLDataTypes.Column(ESQLDataTypes.Float)
    other_income = ESQLDataTypes.Column(ESQLDataTypes.Float)
    account_transfers = ESQLDataTypes.Column(ESQLDataTypes.Float)
    investment_transfers = ESQLDataTypes.Column(ESQLDataTypes.Float)
    savings_transfers = ESQLDataTypes.Column(ESQLDataTypes.Float)
    cash_deposits = ESQLDataTypes.Column(ESQLDataTypes.Float)
    cash_withdrawals = ESQLDataTypes.Column(ESQLDataTypes.Float)
    loans_and_cash_advances = ESQLDataTypes.Column(ESQLDataTypes.Float)
    person_to_person_payments = ESQLDataTypes.Column(ESQLDataTypes.Float)
    other_transfers = ESQLDataTypes.Column(ESQLDataTypes.Float)
    credit_card_payments = ESQLDataTypes.Column(ESQLDataTypes.Float)
    auto_loan_payments = ESQLDataTypes.Column(ESQLDataTypes.Float)
    student_loan_payments = ESQLDataTypes.Column(ESQLDataTypes.Float)
    personal_loan_payments = ESQLDataTypes.Column(ESQLDataTypes.Float)
    other_debt_payments = ESQLDataTypes.Column(ESQLDataTypes.Float)
    buy = ESQLDataTypes.Column(ESQLDataTypes.Float)
    sell = ESQLDataTypes.Column(ESQLDataTypes.Float)
    atm_fees = ESQLDataTypes.Column(ESQLDataTypes.Float)
    foreign_transaction_fees = ESQLDataTypes.Column(ESQLDataTypes.Float)
    insufficient_funds = ESQLDataTypes.Column(ESQLDataTypes.Float)
    interest_charge = ESQLDataTypes.Column(ESQLDataTypes.Float)
    late_fees = ESQLDataTypes.Column(ESQLDataTypes.Float)
    wire_fees = ESQLDataTypes.Column(ESQLDataTypes.Float)
    overdraft_fees = ESQLDataTypes.Column(ESQLDataTypes.Float)
    other_bank_fees = ESQLDataTypes.Column(ESQLDataTypes.Float)
    restaurants_and_bars = ESQLDataTypes.Column(ESQLDataTypes.Float)
    groceries = ESQLDataTypes.Column(ESQLDataTypes.Float)
    coffee_shops = ESQLDataTypes.Column(ESQLDataTypes.Float)
    liquor_stores = ESQLDataTypes.Column(ESQLDataTypes.Float)
    other_food_and_drink = ESQLDataTypes.Column(ESQLDataTypes.Float)
    clothing_and_accessories = ESQLDataTypes.Column(ESQLDataTypes.Float)
    electronics = ESQLDataTypes.Column(ESQLDataTypes.Float)
    pet_supplies = ESQLDataTypes.Column(ESQLDataTypes.Float)
    gifts = ESQLDataTypes.Column(ESQLDataTypes.Float)
    office_supplies = ESQLDataTypes.Column(ESQLDataTypes.Float)
    sports_and_outdoors = ESQLDataTypes.Column(ESQLDataTypes.Float)
    retail = ESQLDataTypes.Column(ESQLDataTypes.Float)
    convenience_stores = ESQLDataTypes.Column(ESQLDataTypes.Float)
    hair_and_beauty = ESQLDataTypes.Column(ESQLDataTypes.Float)
    tabacco_and_vape = ESQLDataTypes.Column(ESQLDataTypes.Float)
    other_shopping = ESQLDataTypes.Column(ESQLDataTypes.Float)
    rent = ESQLDataTypes.Column(ESQLDataTypes.Float)
    mortgage_payments = ESQLDataTypes.Column(ESQLDataTypes.Float)
    home_improvement_and_repairs = ESQLDataTypes.Column(ESQLDataTypes.Float)
    phone_and_internet = ESQLDataTypes.Column(ESQLDataTypes.Float)
    gas_and_electricity = ESQLDataTypes.Column(ESQLDataTypes.Float)
    water_sewer_and_garbage = ESQLDataTypes.Column(ESQLDataTypes.Float)
    security = ESQLDataTypes.Column(ESQLDataTypes.Float)
    hoa_fee = ESQLDataTypes.Column(ESQLDataTypes.Float)
    property_tax = ESQLDataTypes.Column(ESQLDataTypes.Float)
    other_housing_and_utilities = ESQLDataTypes.Column(ESQLDataTypes.Float)
    medical = ESQLDataTypes.Column(ESQLDataTypes.Float)
    pharmacy = ESQLDataTypes.Column(ESQLDataTypes.Float)
    dental = ESQLDataTypes.Column(ESQLDataTypes.Float)
    vision = ESQLDataTypes.Column(ESQLDataTypes.Float)
    nursing = ESQLDataTypes.Column(ESQLDataTypes.Float)
    fitness = ESQLDataTypes.Column(ESQLDataTypes.Float)
    personal_care = ESQLDataTypes.Column(ESQLDataTypes.Float)
    other_health_and_wellness = ESQLDataTypes.Column(ESQLDataTypes.Float)
    gambling = ESQLDataTypes.Column(ESQLDataTypes.Float)
    books_and_news = ESQLDataTypes.Column(ESQLDataTypes.Float)
    movies_and_tv = ESQLDataTypes.Column(ESQLDataTypes.Float)
    music_and_audio = ESQLDataTypes.Column(ESQLDataTypes.Float)
    games = ESQLDataTypes.Column(ESQLDataTypes.Float)
    events_and_recreation = ESQLDataTypes.Column(ESQLDataTypes.Float)
    other_entertainment = ESQLDataTypes.Column(ESQLDataTypes.Float)
    life_insurance = ESQLDataTypes.Column(ESQLDataTypes.Float)
    health_insurance = ESQLDataTypes.Column(ESQLDataTypes.Float)
    auto_insurance = ESQLDataTypes.Column(ESQLDataTypes.Float)
    home_insurance = ESQLDataTypes.Column(ESQLDataTypes.Float)
    other_insurance = ESQLDataTypes.Column(ESQLDataTypes.Float)
    household_services = ESQLDataTypes.Column(ESQLDataTypes.Float)
    education_services = ESQLDataTypes.Column(ESQLDataTypes.Float)
    veterinary_services = ESQLDataTypes.Column(ESQLDataTypes.Float)
    childcare_services = ESQLDataTypes.Column(ESQLDataTypes.Float)
    digital_services = ESQLDataTypes.Column(ESQLDataTypes.Float)
    legal_services = ESQLDataTypes.Column(ESQLDataTypes.Float)
    financial_services = ESQLDataTypes.Column(ESQLDataTypes.Float)
    shipping = ESQLDataTypes.Column(ESQLDataTypes.Float)
    moving_and_storage = ESQLDataTypes.Column(ESQLDataTypes.Float)
    other_services = ESQLDataTypes.Column(ESQLDataTypes.Float)
    gas_and_ev_charging = ESQLDataTypes.Column(ESQLDataTypes.Float)
    car_services = ESQLDataTypes.Column(ESQLDataTypes.Float)
    public_transit = ESQLDataTypes.Column(ESQLDataTypes.Float)
    taxi_and_ride_shares = ESQLDataTypes.Column(ESQLDataTypes.Float)
    parking_and_tolls = ESQLDataTypes.Column(ESQLDataTypes.Float)
    other_transportation = ESQLDataTypes.Column(ESQLDataTypes.Float)
    flights = ESQLDataTypes.Column(ESQLDataTypes.Float)
    hotels = ESQLDataTypes.Column(ESQLDataTypes.Float)
    rental_cars = ESQLDataTypes.Column(ESQLDataTypes.Float)
    other_travel = ESQLDataTypes.Column(ESQLDataTypes.Float)
    tax_payments = ESQLDataTypes.Column(ESQLDataTypes.Float)
    government_fees = ESQLDataTypes.Column(ESQLDataTypes.Float)
    charity = ESQLDataTypes.Column(ESQLDataTypes.Float)
    other_government_and_charity = ESQLDataTypes.Column(ESQLDataTypes.Float)
    other = ESQLDataTypes.Column(ESQLDataTypes.Float)



summary_columns = [
    Column()
]