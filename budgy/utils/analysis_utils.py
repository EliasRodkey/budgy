#!python3
"""
budgy.utils.analysis_utils.py

A utility module for transaction categorization in the budgy budgeting application.
This module provides comprehensive category mappings for financial transactions,
defining both primary and detailed transaction categories along with their relationships.

Classes:
    - PrimaryCategories (Enum): High-level transaction categories including Income,
      Transfers, Debt Payments, Investments, Bank Fees, Food & Drink, Shopping,
      Housing & Utilities, Health & Wellness, Entertainment, Insurance, Services,
      Transportation, Travel, Government & Charity, and Other.
    - DetailedCategories (Enum): Granular subcategories nested under each primary
      category (e.g., Wages, Dividends, Interest under Income; Rent, Mortgage,
      Utilities under Housing & Utilities).

Variables:
    - CATEGORY_MAPPING (Dict): Bidirectional mapping dictionary that links each
      PrimaryCategory to its corresponding list of DetailedCategories, enabling
      transaction classification and hierarchy navigation.
    - REVERSE_CATEGORY_MAPPING (Dict): Inverse mapping dictionary for efficient
      lookup of primary categories from detailed categories.
      
Usage:
    Use these enums and mappings to categorize transactions, validate category
    assignments, and navigate the category hierarchy in financial analysis operations.
"""

# Standard library imports
from enum import Enum

# initialize module logger
import logging
logger = logging.getLogger(__name__)



class CategoriesEnum(str, Enum):
    """Parent class for category enum objects"""

    def __str__(self):
        return str(self.value)
    
    @property
    def as_snake_case_headers(self) -> list:
        return [member.value.lower().replace("&", "and").replace(" ", "_") for member in self]
    
    @property
    def as_list(self) -> list:
        return [member.value for member in self]



class PrimaryCategories(CategoriesEnum):
    """Enum class for primary categories of transactions."""
    INCOME = "Income"
    TRANSFERS = "Transfers"
    DEBT_PAYMENTS = "Debt payments"
    INVESTMENTS = "Investments"
    BANK_FEES = "Bank fees"
    FOOD_AND_DRINK = "Food & drink"
    SHOPPING = "Shopping"
    HOUSING_AND_UTILITIES = "Housing & utilities"
    HEALTH_AND_WELLNESS = "Health & wellness"
    ENTERTAINMENT = "Entertainment"
    INSURANCE = "Insurance"
    SERVICES = "Services"
    TRANSPORTATION = "Transportation"
    TRAVEL = "Travel"
    GOVERNMENT_AND_CHARITY = "Government & charity"
    OTHER = "Other"



class DetailedCategories(CategoriesEnum):
    """Enum class for detailed categories of transactions."""
    # Income subcategories
    WAGES = "Wages"
    DIVIDENDS = "Dividends"
    INTEREST = "Interest"
    BENEFITS_AND_PENSION = "Benefits & pension"
    TAX_REFUNDS = "Tax refunds"
    UNEMPLOYMENT = "Unemployment"
    OTHER_INCOME = "Other income"

    # Transfers subcategories
    ACCOUNT_TRANSFERS = "Account transfers" # Exclude
    INVESTMENT_TRANSFERS = "Investment transfers" # Exclude but track
    SAVINGS_TRANSFERS = "Savings transfers" # Exclude
    CASH_DEPOSITS = "Cash deposits" # Income?
    CASH_WITHDRAWALS = "Cash withdrawals" 
    LOANS_AND_CASH_ADVANCES = "Loans & cash advances" 
    PERSON_TO_PERSON_PAYMENTS = "Person to person payments" # Observe NET? Tie to other transactions?
    OTHER_TRANSFERS = "Other transfers"

    # Debt payments subcategories
    CREDIT_CARD_PAYMENTS = "Credit card payments" # Exclude
    AUTO_LOAN_PAYMENTS = "Auto loan payments"
    STUDENT_LOAN_PAYMENTS = "Student loan payments"
    PERSONAL_LOAN_PAYMENTS = "Personal loan payments"
    OTHER_DEBT_PAYMENTS = "Other debt payments"

    # Inevestments subcategories
    BUY = "Buy"
    SELL = "Sell"

    # Bank fees subcategories
    ATM_FEES = "Atm fees"
    FOREIGN_TRANSACTION_FEES = "Foreign transaction fees"
    INSUFFICIENT_FUNDS = "Insufficient funds"
    INTEREST_CHARGE = "Interest charge"
    LATE_FEES = "Late fees"
    WIRE_FEES = "Wire fees"
    OVERDRAFT_FEES = "Overdraft fees"
    OTHER_BANK_FEES = "Other bank fees"
    
    # Food & drink subcategories
    RESTAURANTS_AND_BARS = "Restaurants & bars"
    GROCERIES = "Groceries"
    COFFEE_SHOPS = "Coffee shops"
    LIQUOR_STORES = "Liquor stores"
    OTHER_FOOD_AND_DRINK = "Other food & drink"

    # Shopping subcategories
    CLOTHING_AND_ACCESSORIES = "Clothing & accessories"
    ELECTRONICS = "Electronics"
    PET_SUPPLIES = "Pet supplies"
    GIFTS = "Gifts"
    OFFICE_SUPPLIES = "Office supplies"
    SPORTS_AND_OUTDOORS = "Sports & outdoors"
    RETAIL = "Retail"
    CONVIENIENCE_STORES = "Convenience stores"
    HAIR_AND_BEAUTY = "Hair & beauty"
    TABACCO_AND_VAPE = "Tabacco & vape"
    OTHER_SHOPPING = "Other shopping"

    # Housing & utilities subcategories
    RENT = "Rent"
    MORTGAGE_PAYMENTS = "Mortgage payments"
    HOME_IMPROVEMENT_AND_REPAIRS = "Home improvement & repairs"
    PHONE_AMD_INTERNET = "Phone & internet"
    GAS_AND_ELECTRICITY = "Gas & electricity"
    WATER_SEWER_AND_GARBAGE = "Water sewer & garbage"
    SECURITY = "Security"
    HOA_FEE = "Hoa fee"
    PROPERTY_TAX = "Property tax"
    OTHER_HOUSING_AND_UTILITIES = "Other housing & utilities"

    # Health & wellness subcategories
    MEDICAL = "Medical"
    PHARMACY = "Pharmacy"
    DENTAL = "Dental"
    VISION = "Vision"
    NURSING = "Nursing"
    FITNESS = "Fitness"
    PERSONAL_CARE = "Personal care"
    OTHER_HEALTH_AND_WELLNESS = "Other health & wellness"

    # Entertainment subcategories
    GAMBLING = "Gambling"
    BOOKS_AND_NEWS = "Books & news"
    MOVIES_AND_TV = "Movies & tv"
    MUSIC_AND_AUDIO = "Music & audio"
    GAMES = "Games"
    EVENTS_AND_RECREATION = "Events & recreation"
    OTHER_ENTERTAINMENT = "Other entertainment"

    # Insurance subcategories
    LIFE_INSURANCE = "Life insurance"
    HEALTH_INSURANCE = "Health insurance"
    AUTO_INSURANCE = "Auto insurance"
    HOME_INSURANCE = "Home insurance"
    OTHER_INSURANCE = "Other insurance"

    # Services subcategories
    HOUSEHOLFD_SERVICES = "Household services"
    EDUCATION_SERVICES = "Education services"
    VETERINARY_SERVICES = "Veterinary services"
    CHILDCHILD_SERVICES = "Childcare services"
    DIGITAL_SERVICES = "Digital services"
    LEGAL_SERVICES = "Legal services"
    FINANCIAL_SERVICES = "Financial services"
    SHIPPING = "Shipping"
    MOVING_AND_STORAGE = "Moving & storage"
    OTHER_SERVICES = "Other services"

    # Transportation subcategories
    GAS_AND_EV_CHARGING = "Gas & ev charging"
    CAR_SERVICES = "Car services"
    PUBLIC_TRANSIT = "Public transit"
    TAXI_AND_RIDE_SHARES = "Taxi & ride shares"
    PARKING_AND_TOLLS = "Parking & tolls"
    OTHER_TRANSPORTATION = "Other transportation"

    # Travel subcategories
    FLIGHTS = "Flights"
    HOTELS = "Hotels"
    RENTAL_CARS = "Rental cars"
    OTHER_TRAVEL = "Other travel"

    # Government & charity subcategories
    TAX_PAYMENTS = "Tax payments"
    GOVERNMENT_FEES = "Government fees"
    CHARITY = "Charity"
    OTHER_GOVERNMENT_AND_CHARITY = "Other government & charity"

    # Other subcategories
    OTHER = "Other"


# Mapping of primary categories to the detailed categories that fall under them
CATEGORY_MAPPING = {
    PrimaryCategories.INCOME: [
        DetailedCategories.WAGES,
        DetailedCategories.DIVIDENDS,
        DetailedCategories.INTEREST,
        DetailedCategories.BENEFITS_AND_PENSION,
        DetailedCategories.TAX_REFUNDS,
        DetailedCategories.UNEMPLOYMENT,
        DetailedCategories.OTHER_INCOME
    ],
    PrimaryCategories.TRANSFERS: [
        DetailedCategories.ACCOUNT_TRANSFERS,
        DetailedCategories.INVESTMENT_TRANSFERS,
        DetailedCategories.SAVINGS_TRANSFERS,
        DetailedCategories.CASH_DEPOSITS,
        DetailedCategories.CASH_WITHDRAWALS,
        DetailedCategories.LOANS_AND_CASH_ADVANCES,
        DetailedCategories.PERSON_TO_PERSON_PAYMENTS,
        DetailedCategories.OTHER_TRANSFERS
    ],
    PrimaryCategories.DEBT_PAYMENTS: [
        DetailedCategories.CREDIT_CARD_PAYMENTS,
        DetailedCategories.AUTO_LOAN_PAYMENTS,
        DetailedCategories.STUDENT_LOAN_PAYMENTS,
        DetailedCategories.PERSONAL_LOAN_PAYMENTS,
        DetailedCategories.OTHER_DEBT_PAYMENTS
    ],
    PrimaryCategories.INVESTMENTS: [
        DetailedCategories.BUY,
        DetailedCategories.SELL
    ],
    PrimaryCategories.BANK_FEES: [
        DetailedCategories.ATM_FEES,
        DetailedCategories.FOREIGN_TRANSACTION_FEES,
        DetailedCategories.INSUFFICIENT_FUNDS,
        DetailedCategories.INTEREST_CHARGE,
        DetailedCategories.LATE_FEES,
        DetailedCategories.WIRE_FEES,
        DetailedCategories.OVERDRAFT_FEES,
        DetailedCategories.OTHER_BANK_FEES
    ],
    PrimaryCategories.FOOD_AND_DRINK: [
        DetailedCategories.RESTAURANTS_AND_BARS,
        DetailedCategories.GROCERIES,
        DetailedCategories.COFFEE_SHOPS,
        DetailedCategories.LIQUOR_STORES,
        DetailedCategories.OTHER_FOOD_AND_DRINK
    ],
    PrimaryCategories.SHOPPING: [
        DetailedCategories.CLOTHING_AND_ACCESSORIES,
        DetailedCategories.ELECTRONICS,
        DetailedCategories.PET_SUPPLIES,
        DetailedCategories.GIFTS,
        DetailedCategories.OFFICE_SUPPLIES,
        DetailedCategories.SPORTS_AND_OUTDOORS,
        DetailedCategories.RETAIL,
        DetailedCategories.CONVIENIENCE_STORES,
        DetailedCategories.HAIR_AND_BEAUTY,
        DetailedCategories.TABACCO_AND_VAPE,
        DetailedCategories.OTHER_SHOPPING
    ],
    PrimaryCategories.HOUSING_AND_UTILITIES: [
        DetailedCategories.RENT,
        DetailedCategories.MORTGAGE_PAYMENTS,
        DetailedCategories.HOME_IMPROVEMENT_AND_REPAIRS,
        DetailedCategories.PHONE_AMD_INTERNET,
        DetailedCategories.GAS_AND_ELECTRICITY,
        DetailedCategories.WATER_SEWER_AND_GARBAGE,
        DetailedCategories.SECURITY,
        DetailedCategories.HOA_FEE,
        DetailedCategories.PROPERTY_TAX,
        DetailedCategories.OTHER_HOUSING_AND_UTILITIES
    ],
    PrimaryCategories.HEALTH_AND_WELLNESS: [
        DetailedCategories.MEDICAL,
        DetailedCategories.PHARMACY,
        DetailedCategories.DENTAL,
        DetailedCategories.VISION,
        DetailedCategories.NURSING,
        DetailedCategories.FITNESS,
        DetailedCategories.PERSONAL_CARE,
        DetailedCategories.OTHER_HEALTH_AND_WELLNESS
    ],
    PrimaryCategories.ENTERTAINMENT: [
        DetailedCategories.GAMBLING,
        DetailedCategories.BOOKS_AND_NEWS,
        DetailedCategories.MOVIES_AND_TV,
        DetailedCategories.MUSIC_AND_AUDIO,
        DetailedCategories.GAMES,
        DetailedCategories.EVENTS_AND_RECREATION,
        DetailedCategories.OTHER_ENTERTAINMENT
    ],
    PrimaryCategories.INSURANCE: [
        DetailedCategories.LIFE_INSURANCE,
        DetailedCategories.HEALTH_INSURANCE,
        DetailedCategories.AUTO_INSURANCE,
        DetailedCategories.HOME_INSURANCE,
        DetailedCategories.OTHER_INSURANCE
    ],
    PrimaryCategories.SERVICES: [
        DetailedCategories.HOUSEHOLFD_SERVICES,
        DetailedCategories.EDUCATION_SERVICES,
        DetailedCategories.VETERINARY_SERVICES,
        DetailedCategories.CHILDCHILD_SERVICES,
        DetailedCategories.DIGITAL_SERVICES,
        DetailedCategories.LEGAL_SERVICES,
        DetailedCategories.FINANCIAL_SERVICES,
        DetailedCategories.SHIPPING,
        DetailedCategories.MOVING_AND_STORAGE,
        DetailedCategories.OTHER_SERVICES
    ],
    PrimaryCategories.TRANSPORTATION: [
        DetailedCategories.GAS_AND_EV_CHARGING,
        DetailedCategories.CAR_SERVICES,
        DetailedCategories.PUBLIC_TRANSIT,
        DetailedCategories.TAXI_AND_RIDE_SHARES,
        DetailedCategories.PARKING_AND_TOLLS,
        DetailedCategories.OTHER_TRANSPORTATION
    ],
    PrimaryCategories.TRAVEL: [
        DetailedCategories.FLIGHTS,
        DetailedCategories.HOTELS,
        DetailedCategories.RENTAL_CARS,
        DetailedCategories.OTHER_TRAVEL
    ],
    PrimaryCategories.GOVERNMENT_AND_CHARITY: [
        DetailedCategories.TAX_PAYMENTS,
        DetailedCategories.GOVERNMENT_FEES,
        DetailedCategories.CHARITY,
        DetailedCategories.OTHER_GOVERNMENT_AND_CHARITY
    ],
    PrimaryCategories.OTHER: [
        DetailedCategories.OTHER
    ]
}

# The opposite of the above mapping, for looking up primary categories by detailed category
REVERSE_CATEGORY_MAPPING = {detailed: primary for primary, detailed_list in CATEGORY_MAPPING.items() for detailed in detailed_list}

EXCLUDE_CATEGORIES = [
    DetailedCategories.ACCOUNT_TRANSFERS, 
    DetailedCategories.CREDIT_CARD_PAYMENTS, 
    DetailedCategories.INVESTMENT_TRANSFERS,
    DetailedCategories.SAVINGS_TRANSFERS
]