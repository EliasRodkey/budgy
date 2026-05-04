#!python3
"""
backend.utils.api_utils
Contians utility functions for API endpoints, such as pagination, filtering helpers, and enums.
"""
# Standard library imports
from enum import Enum

class RouterPrefixes(Enum):
    """
    Enum for router prefixes to ensure consistency across the application.
    """
    TRANSACTIONS = "/transactions"
    CATEGORIES = "/categories"
    BUDGETS = "/budgets"
    SUMMARIES = "/summaries"
    ANALYTICS = "/analytics"
    AI = "/ai"