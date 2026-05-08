#!python3
"""
Tests for CategoryMappingRulesManager.

Covers:
    - upsert_column_rule: create and update
    - upsert_category_rule: create and update
    - get_column_rule: found and not found
    - get_category_rule: found and not found
    - rule_type isolation: column and category rules don't collide
    - list_rules: empty and populated
"""
import pytest

from pleasant_database import DatabaseFile
from backend.database_modules.managers.category_mapping_rules_manager import CategoryMappingRulesManager
from backend.tests.conftest import TEST_DB_DIR, TEST_DB_FILEPATH


@pytest.fixture()
def mgr():
    """Fresh CategoryMappingRulesManager backed by the shared test DB; cleared after each test."""
    db_file = DatabaseFile(TEST_DB_FILEPATH, TEST_DB_DIR)
    manager = CategoryMappingRulesManager(db_file)
    yield manager
    manager.clear_table()
    manager.end_session()


# ── upsert_column_rule ────────────────────────────────────────────────────────

class TestUpsertColumnRule:
    def test_creates_new_column_rule(self, mgr):
        rule = mgr.upsert_column_rule("Txn Date", "authorized_date")
        assert rule.id is not None
        assert rule.rule_type == "column"
        assert rule.raw_value == "Txn Date"
        assert rule.mapped_column == "authorized_date"

    def test_updates_existing_column_rule(self, mgr):
        mgr.upsert_column_rule("Date", "authorized_date")
        updated = mgr.upsert_column_rule("Date", "posted_date")
        assert updated.mapped_column == "posted_date"

    def test_upsert_does_not_duplicate_column_rule(self, mgr):
        mgr.upsert_column_rule("Debit", "amount")
        mgr.upsert_column_rule("Debit", "amount")
        assert len(mgr.list_rules()) == 1

    def test_different_raw_values_create_separate_column_rules(self, mgr):
        mgr.upsert_column_rule("Date", "authorized_date")
        mgr.upsert_column_rule("Posted Date", "posted_date")
        assert len(mgr.list_rules()) == 2


# ── upsert_category_rule ──────────────────────────────────────────────────────

class TestUpsertCategoryRule:
    def test_creates_new_category_rule(self, mgr):
        rule = mgr.upsert_category_rule("Dining Out", "Food & Drink", "Restaurants & Bars")
        assert rule.id is not None
        assert rule.rule_type == "category"
        assert rule.raw_value == "Dining Out"
        assert rule.primary_cat == "Food & Drink"
        assert rule.detailed_cat == "Restaurants & Bars"

    def test_updates_existing_category_rule(self, mgr):
        mgr.upsert_category_rule("Gas", "Transportation", "Gas & Fuel")
        updated = mgr.upsert_category_rule("Gas", "Transportation", "Other Transportation")
        assert updated.detailed_cat == "Other Transportation"
        assert updated.primary_cat == "Transportation"

    def test_upsert_does_not_duplicate_category_rule(self, mgr):
        mgr.upsert_category_rule("Groceries", "Food & Drink", "Groceries")
        mgr.upsert_category_rule("Groceries", "Food & Drink", "Groceries")
        assert len(mgr.list_rules()) == 1


# ── get_column_rule ───────────────────────────────────────────────────────────

class TestGetColumnRule:
    def test_returns_mapped_column_when_found(self, mgr):
        mgr.upsert_column_rule("Transaction Date", "authorized_date")
        result = mgr.get_column_rule("Transaction Date")
        assert result == "authorized_date"

    def test_returns_none_when_not_found(self, mgr):
        assert mgr.get_column_rule("Unknown Header") is None


# ── get_category_rule ─────────────────────────────────────────────────────────

class TestGetCategoryRule:
    def test_returns_primary_and_detailed_when_found(self, mgr):
        mgr.upsert_category_rule("Coffee", "Food & Drink", "Coffee Shops")
        result = mgr.get_category_rule("Coffee")
        assert result == {"primary": "Food & Drink", "detailed": "Coffee Shops"}

    def test_returns_none_when_not_found(self, mgr):
        assert mgr.get_category_rule("Nonexistent Category") is None


# ── rule_type isolation ───────────────────────────────────────────────────────

class TestRuleTypeIsolation:
    def test_same_raw_value_can_exist_as_both_column_and_category(self, mgr):
        """'Amount' could theoretically appear as both a column header and a category string."""
        mgr.upsert_column_rule("Amount", "amount")
        mgr.upsert_category_rule("Amount", "Other", "Other Expenses")
        assert len(mgr.list_rules()) == 2

    def test_get_column_rule_does_not_return_category_rule(self, mgr):
        mgr.upsert_category_rule("Shopping", "Shopping", "Online Shopping")
        assert mgr.get_column_rule("Shopping") is None

    def test_get_category_rule_does_not_return_column_rule(self, mgr):
        mgr.upsert_column_rule("Category", "primary_category")
        assert mgr.get_category_rule("Category") is None


# ── list_rules ────────────────────────────────────────────────────────────────

class TestListRules:
    def test_returns_empty_list_when_no_rules(self, mgr):
        assert mgr.list_rules() == []

    def test_returns_all_rules_of_both_types(self, mgr):
        mgr.upsert_column_rule("Date", "authorized_date")
        mgr.upsert_column_rule("Debit", "amount")
        mgr.upsert_category_rule("Dining", "Food & Drink", "Restaurants & Bars")
        assert len(mgr.list_rules()) == 3
