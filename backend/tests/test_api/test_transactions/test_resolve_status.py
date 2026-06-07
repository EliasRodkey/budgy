#!python3
"""
Pure unit tests for _resolve_status() — determines whether a transaction row
should be considered "Verified" or remain "Unchecked" based on field completeness
and category validity. No database, no HTTP client required.
"""
from datetime import datetime

from backend.api.transactions.transactions_router import _resolve_status
from backend.database_modules.models.transactions import TransactionsTable
from backend.utils.analysis_utils import DetailedCategories, PrimaryCategories


def make_row(**overrides) -> dict:
    row = {
        TransactionsTable.description.name: "Costco Wholesale",
        TransactionsTable.amount.name: -143.27,
        TransactionsTable.authorized_date.name: datetime(2024, 10, 15),
        TransactionsTable.primary_category.name: PrimaryCategories.FOOD_AND_DRINK.value,
        TransactionsTable.detailed_category.name: DetailedCategories.GROCERIES.value,
    }
    row.update(overrides)
    return row


class TestResolveStatus:
    def test_verified_when_all_fields_present_and_valid(self):
        assert _resolve_status(make_row()) == "Verified"

    def test_unchecked_when_description_missing(self):
        assert _resolve_status(make_row(**{TransactionsTable.description.name: ""})) == "Unchecked"

    def test_unchecked_when_amount_missing(self):
        assert _resolve_status(make_row(**{TransactionsTable.amount.name: None})) == "Unchecked"

    def test_unchecked_when_detailed_category_missing(self):
        assert _resolve_status(make_row(**{TransactionsTable.detailed_category.name: None})) == "Unchecked"

    def test_unchecked_when_primary_category_unrecognised(self):
        row = make_row(**{TransactionsTable.primary_category.name: "Not a real category"})
        assert _resolve_status(row) == "Unchecked"

    def test_unchecked_when_detailed_category_unrecognised(self):
        row = make_row(**{TransactionsTable.detailed_category.name: "Not a real detailed category"})
        assert _resolve_status(row) == "Unchecked"
