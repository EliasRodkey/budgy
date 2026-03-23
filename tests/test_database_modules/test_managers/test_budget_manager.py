#!python3
"""
tests.test_database_modules.test_managers.test_budget_manager.py

Tests for budgy.database_modules.managers.budget_manager.py — BudgetsTableManager.
"""
# Standard library imports
import datetime

# Third party imports
import pytest

# Local imports
from budgy.database_modules.managers.common import DuplicateError
from budgy.database_modules.models.budgets import BudgetsTable
from budgy.utils.analysis_utils import PrimaryCategories
from tests.conftest import (
    test_budgets_manager,
    clean_budgets_database,
)

# Initialize module logger
import logging
logger = logging.getLogger(__name__)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _make_sample_budget() -> dict:
    """Returns a full budget dict with all 16 categories set to 100.0."""
    return {cat: 100.0 for cat in PrimaryCategories.as_snake_case_headers()}


def _make_db_budget(uq_hash: str = "abc123deadbeef") -> dict:
    """Returns a full budget dict ready for direct DB insertion (includes date_created and uq_hash)."""
    d = _make_sample_budget()
    d['date_created'] = datetime.datetime(2024, 1, 1)
    d['uq_hash'] = uq_hash
    return d


# ─── TestCleanBudget ──────────────────────────────────────────────────────────

class TestCleanBudget:

    def test_returns_complete_dict_with_all_categories(self):
        """_clean_budget returns a dict with exactly the 16 snake_case category keys."""
        result = test_budgets_manager._clean_budget(_make_sample_budget())
        assert set(result.keys()) == set(PrimaryCategories.as_snake_case_headers())

    def test_accepts_full_valid_budget(self):
        """_clean_budget does not raise for a fully valid 16-category dict."""
        result = test_budgets_manager._clean_budget(_make_sample_budget())
        assert len(result) == len(PrimaryCategories.as_snake_case_headers())

    def test_fills_missing_categories_with_zero(self):
        """_clean_budget fills any missing category key with 0.0."""
        budget = _make_sample_budget()
        missing_key = PrimaryCategories.as_snake_case_headers()[0]
        del budget[missing_key]

        result = test_budgets_manager._clean_budget(budget)
        assert result[missing_key] == 0.0

    def test_raises_on_wrong_value_type(self):
        """_clean_budget raises AssertionError when a category value is not a float."""
        budget = _make_sample_budget()
        budget['income'] = 100  # int, not float
        with pytest.raises(AssertionError):
            test_budgets_manager._clean_budget(budget)

    def test_raises_on_invalid_field(self):
        """_clean_budget raises ValueError when the dict contains an unrecognised key."""
        budget = _make_sample_budget()
        budget['not_a_real_category'] = 0.0
        with pytest.raises(ValueError):
            test_budgets_manager._clean_budget(budget)

    def test_raises_on_extra_valid_looking_field(self):
        """_clean_budget raises ValueError when there are more keys than PrimaryCategories."""
        budget = _make_sample_budget()
        budget['extra_column'] = 50.0  # not a valid category
        with pytest.raises(ValueError):
            test_budgets_manager._clean_budget(budget)


# ─── TestBudgetExistsById ─────────────────────────────────────────────────────

class TestBudgetExistsById:

    def test_returns_false_when_id_not_in_table(self, clean_budgets_database):
        """_budget_exists_by_id returns False for an ID that does not exist."""
        assert clean_budgets_database._budget_exists_by_id(9999) is False

    def test_returns_true_when_id_exists(self, clean_budgets_database):
        """_budget_exists_by_id returns True after a row is inserted directly."""
        clean_budgets_database.add_item(**_make_db_budget())
        item = clean_budgets_database.fetch_all_items()[0]
        assert clean_budgets_database._budget_exists_by_id(item.id) is True

    def test_return_type_is_bool(self, clean_budgets_database):
        """_budget_exists_by_id always returns a bool."""
        result = clean_budgets_database._budget_exists_by_id(1)
        assert isinstance(result, bool)


# ─── TestUqHashExists ─────────────────────────────────────────────────────────

class TestUqHashExists:

    def test_returns_false_when_hash_not_in_table(self, clean_budgets_database):
        """_uq_hash_exists returns False on an empty table."""
        assert clean_budgets_database._uq_hash_exists("nonexistent_hash") is False

    def test_returns_true_when_hash_exists(self, clean_budgets_database):
        """_uq_hash_exists returns True after a row with that hash is inserted."""
        known_hash = "cafebabe1234567890abcdef"
        clean_budgets_database.add_item(**_make_db_budget(uq_hash=known_hash))
        assert clean_budgets_database._uq_hash_exists(known_hash) is True

    def test_returns_false_for_different_hash(self, clean_budgets_database):
        """_uq_hash_exists returns False when querying a hash different from what was inserted."""
        clean_budgets_database.add_item(**_make_db_budget(uq_hash="hashA"))
        assert clean_budgets_database._uq_hash_exists("hashB") is False

    def test_return_type_is_bool(self, clean_budgets_database):
        """_uq_hash_exists always returns a bool."""
        result = clean_budgets_database._uq_hash_exists("anyhash")
        assert isinstance(result, bool)


# ─── TestUploadBudget ─────────────────────────────────────────────────────────

class TestUploadBudget:

    def test_uploads_valid_budget(self, clean_budgets_database):
        """upload_budget inserts one row into the budgets table."""
        clean_budgets_database.upload_budget(_make_sample_budget())
        items = clean_budgets_database.fetch_all_items()
        assert len(items) == 1

    def test_uploaded_budget_has_correct_category_values(self, clean_budgets_database):
        """upload_budget stores category values matching the input dict."""
        budget = _make_sample_budget()
        clean_budgets_database.upload_budget(budget)
        item = clean_budgets_database.fetch_all_items()[0]
        for category in PrimaryCategories.as_snake_case_headers():
            assert getattr(item, category) == budget[category]

    def test_uploaded_budget_has_uq_hash(self, clean_budgets_database):
        """upload_budget stores a 64-character SHA256 hex string as uq_hash."""
        clean_budgets_database.upload_budget(_make_sample_budget())
        item = clean_budgets_database.fetch_all_items()[0]
        assert isinstance(item.uq_hash, str)
        assert len(item.uq_hash) == 64

    def test_uploaded_budget_has_date_created(self, clean_budgets_database):
        """upload_budget auto-generates a datetime for date_created when not provided."""
        clean_budgets_database.upload_budget(_make_sample_budget())
        item = clean_budgets_database.fetch_all_items()[0]
        assert isinstance(item.date_created, datetime.datetime)

    def test_accepts_explicit_date_created(self, clean_budgets_database):
        """upload_budget stores the explicit date_created value when provided."""
        budget = _make_sample_budget()
        expected_date = datetime.datetime(2024, 6, 15)
        budget['date_created'] = expected_date
        clean_budgets_database.upload_budget(budget)
        item = clean_budgets_database.fetch_all_items()[0]
        assert item.date_created == expected_date

    def test_raises_duplicate_error_on_same_budget(self, clean_budgets_database):
        """upload_budget raises DuplicateError when the same budget is uploaded twice."""
        clean_budgets_database.upload_budget(_make_sample_budget())
        with pytest.raises(DuplicateError):
            clean_budgets_database.upload_budget(_make_sample_budget())

    def test_does_not_upload_invalid_budget(self, clean_budgets_database):
        """upload_budget raises ValueError for invalid fields and leaves the table empty."""
        budget = _make_sample_budget()
        budget['bad_field'] = 0.0
        with pytest.raises(ValueError):
            clean_budgets_database.upload_budget(budget)
        assert len(clean_budgets_database.fetch_all_items()) == 0

    def test_raises_on_invalid_date_created_type(self, clean_budgets_database):
        """upload_budget raises AssertionError when date_created is not a datetime."""
        budget = _make_sample_budget()
        budget['date_created'] = "2024-01-01"  # string, not datetime
        with pytest.raises(AssertionError):
            clean_budgets_database.upload_budget(budget)


# ─── TestFetchBudgetById ──────────────────────────────────────────────────────

class TestFetchBudgetById:

    def test_returns_budget_table_class_when_not_found(self, clean_budgets_database):
        """fetch_budget_by_id returns the BudgetsTable class (not an instance) for a missing ID."""
        result = clean_budgets_database.fetch_budget_by_id(9999)
        assert result is BudgetsTable

    def test_logs_warning_when_not_found(self, clean_budgets_database, caplog):
        """fetch_budget_by_id logs a warning when the requested ID does not exist."""
        with caplog.at_level(logging.WARNING, logger="budgy.database_modules.managers.budget_manager"):
            clean_budgets_database.fetch_budget_by_id(9999)
        assert any("No budget exists with ID" in message for message in caplog.messages)

    def test_returns_budget_instance_when_found(self, clean_budgets_database):
        """fetch_budget_by_id returns a BudgetsTable instance for an existing budget."""
        clean_budgets_database.upload_budget(_make_sample_budget())
        item = clean_budgets_database.fetch_all_items()[0]
        result = clean_budgets_database.fetch_budget_by_id(item.id)
        assert isinstance(result, BudgetsTable)
