#!python3
"""
tests.test_database_modules.test_managers.test_budget_manager.py

Tests for backend.database_modules.managers.budget_manager.py — BudgetsTableManager.
"""
# Standard library imports
import datetime

# Third party imports
import pytest

# Local imports
from backend.database_modules.managers.common import DuplicateError
from backend.database_modules.models.budgets import BudgetsTable
from backend.utils.analysis_utils import PrimaryCategories
from backend.tests.conftest import (
    test_budgets_manager,
    clean_budgets_database,
)

# Initialize module logger
from pleasant_loggers import get_logger
logger = get_logger(__name__)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _make_sample_budget() -> dict:
    """Returns a full budget dict with all 16 categories set to 100.0."""
    return {cat: 100.0 for cat in PrimaryCategories.as_snake_case_headers()}


def _make_db_budget_record(uq_hash: str = "abc123deadbeef") -> dict:
    """Returns a full budget dict ready for direct DB insertion (includes date_created and uq_hash)."""
    d = _make_sample_budget()
    d['date_created'] = datetime.datetime(2024, 1, 1)
    d['uq_hash'] = uq_hash
    return d


# ─── TestCleanBudget ──────────────────────────────────────────────────────────

class TestCleanBudget:

    def test_valid_budget_output(self):
        """_clean_budget returns a dict with exactly the 16 snake_case category keys and correct length."""
        result = test_budgets_manager._clean_budget(_make_sample_budget())
        assert set(result.keys()) == set(PrimaryCategories.as_snake_case_headers())
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

    def test_raises_on_invalid_keys(self):
        """_clean_budget raises ValueError for any unrecognised or extra key."""
        budget_invalid = _make_sample_budget()
        budget_invalid['not_a_real_category'] = 0.0
        with pytest.raises(ValueError):
            test_budgets_manager._clean_budget(budget_invalid)

        budget_extra = _make_sample_budget()
        budget_extra['extra_column'] = 50.0
        with pytest.raises(ValueError):
            test_budgets_manager._clean_budget(budget_extra)


# ─── TestBudgetExistsById ─────────────────────────────────────────────────────

class TestBudgetExistsById:

    def test_returns_false_and_is_bool_on_empty_table(self, clean_budgets_database):
        """_budget_exists_by_id returns False (and a bool) for an ID that does not exist."""
        result = clean_budgets_database._budget_exists_by_id(9999)
        assert result is False
        assert isinstance(result, bool)

    def test_returns_true_when_id_exists(self, clean_budgets_database):
        """_budget_exists_by_id returns True after a row is inserted directly."""
        clean_budgets_database.add_item(**_make_db_budget_record())
        item = clean_budgets_database.fetch_all_items()[0]
        assert clean_budgets_database._budget_exists_by_id(item.id) is True


# ─── TestUqHashExists ─────────────────────────────────────────────────────────

class TestUqHashExists:

    def test_returns_false_and_is_bool_on_empty_table(self, clean_budgets_database):
        """_uq_hash_exists returns False (and a bool) when no matching hash is in the table."""
        result = clean_budgets_database._uq_hash_exists("nonexistent_hash")
        assert result is False
        assert isinstance(result, bool)

    def test_with_seeded_hash(self, clean_budgets_database):
        """True for the inserted hash; False for a different hash."""
        known_hash = "cafebabe1234567890abcdef"
        clean_budgets_database.add_item(**_make_db_budget_record(uq_hash=known_hash))
        assert clean_budgets_database._uq_hash_exists(known_hash) is True
        assert clean_budgets_database._uq_hash_exists("hashB") is False


# ─── TestUploadBudget ─────────────────────────────────────────────────────────

class TestUploadBudget:

    def test_upload_valid_budget(self, clean_budgets_database):
        """upload_budget inserts one row with correct category values, a 64-char uq_hash, and a datetime date_created."""
        budget = _make_sample_budget()
        clean_budgets_database.upload_budget(budget)
        items = clean_budgets_database.fetch_all_items()
        assert len(items) == 1
        item = items[0]
        for category in PrimaryCategories.as_snake_case_headers():
            assert getattr(item, category) == budget[category]
        assert isinstance(item.uq_hash, str)
        assert len(item.uq_hash) == 64
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

    def test_not_found_returns_class_and_warns(self, clean_budgets_database, caplog):
        """fetch_budget_by_id returns the BudgetsTable class and logs a warning for a missing ID."""
        with caplog.at_level(logging.WARNING, logger="backend.database_modules.managers.budget_manager"):
            result = clean_budgets_database.fetch_budget_by_id(9999)
        assert result is BudgetsTable
        assert any("No budget exists with ID" in message for message in caplog.messages)

    def test_returns_budget_instance_when_found(self, clean_budgets_database):
        """fetch_budget_by_id returns a BudgetsTable instance for an existing budget."""
        clean_budgets_database.upload_budget(_make_sample_budget())
        item = clean_budgets_database.fetch_all_items()[0]
        result = clean_budgets_database.fetch_budget_by_id(item.id)
        assert isinstance(result, BudgetsTable)


# ─── TestCalculateNetGainOrLoss ───────────────────────────────────────────────

class TestCalculateNetGainOrLoss:

    def test_returns_correct_float_for_all_scenarios(self):
        """calculate_net_gain_or_loss returns the correct float for loss, gain, and breakeven.

        Base setup: all 16 categories = 100.0.
        Total spending = 15 non-income categories × 100.0 = 1500.0.
          income=100.0  → net = 100 - 1500 = -1400.0  (loss)
          income=2000.0 → net = 2000 - 1500 = 500.0   (gain)
          income=1500.0 → net = 1500 - 1500 = 0.0     (breakeven)
        """
        budget = _make_db_budget_record()  # all 16 categories = 100.0, includes uq_hash

        budget["income"] = 100.0
        result_loss = test_budgets_manager.calculate_net_gain_or_loss(budget)
        assert result_loss == -1400.0
        assert isinstance(result_loss, float)

        budget["income"] = 2000.0
        result_gain = test_budgets_manager.calculate_net_gain_or_loss(budget)
        assert result_gain == 500.0

        budget["income"] = 1500.0
        result_breakeven = test_budgets_manager.calculate_net_gain_or_loss(budget)
        assert result_breakeven == 0.0
