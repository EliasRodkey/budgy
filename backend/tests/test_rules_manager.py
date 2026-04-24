#!python3
"""
Tests for TransactionRulesManager.

Covers:
    - upsert_rule: create, update (idempotent upsert)
    - get_rule: found and not found
    - list_rules: empty and populated
    - update_rule: field patching, auto updated_at, list coercion
    - delete_rule: removes the record
    - apply_rules_to_transaction / apply_rules_to_all: stubs (no-op, no exceptions)
"""
import pytest
from datetime import datetime

from pleasant_database import DatabaseFile
from backend.database_modules.managers.rules_manager import TransactionRulesManager
from backend.tests.conftest import TEST_DB_DIR, TEST_DB_FILENAME, TEST_DB_FILEPATH


@pytest.fixture()
def rules_manager():
    """Fresh RulesManager backed by the shared test DB; table cleared after each test."""
    db_file = DatabaseFile(TEST_DB_FILEPATH, TEST_DB_DIR)
    manager = TransactionRulesManager(db_file)
    yield manager
    manager.clear_table()
    manager.end_session()


# ── upsert_rule ───────────────────────────────────────────────────────────────

class TestUpsertRule:
    def test_creates_new_rule(self, rules_manager):
        rule = rules_manager.upsert_rule(
            match_description="TRADER JOES",
            match_account_name="Chase Sapphire",
            primary_category="Food & drink",
            detailed_category="Groceries",
            tags=["groceries"],
        )
        assert rule.id is not None
        assert rule.match_description == "TRADER JOES"
        assert rule.match_account_name == "Chase Sapphire"
        assert rule.primary_category == "Food & drink"
        assert rule.detailed_category == "Groceries"
        assert rule.tags == "groceries"
        assert rule.match_type == "exact"

    def test_updates_existing_rule_on_second_call(self, rules_manager):
        rules_manager.upsert_rule(
            match_description="NETFLIX",
            match_account_name="SoFi Checking",
            primary_category="Entertainment",
        )
        updated = rules_manager.upsert_rule(
            match_description="NETFLIX",
            match_account_name="SoFi Checking",
            detailed_category="Streaming",
            tags=["subscription"],
        )
        assert updated.primary_category == "Entertainment"  # preserved
        assert updated.detailed_category == "Streaming"     # updated
        assert updated.tags == "subscription"               # updated

    def test_upsert_does_not_create_duplicate_rows(self, rules_manager):
        rules_manager.upsert_rule("STARBUCKS", "Chase Freedom")
        rules_manager.upsert_rule("STARBUCKS", "Chase Freedom", primary_category="Food & drink")
        assert len(rules_manager.list_rules()) == 1

    def test_tags_stored_as_comma_separated_string(self, rules_manager):
        rule = rules_manager.upsert_rule(
            "AMAZON", "Chase Sapphire", tags=["shopping", "online", "prime"]
        )
        assert rule.tags == "shopping,online,prime"

    def test_rule_with_no_optional_fields(self, rules_manager):
        rule = rules_manager.upsert_rule("VENMO", "SoFi Checking")
        assert rule.primary_category is None
        assert rule.detailed_category is None
        assert rule.tags is None

    def test_different_account_names_create_separate_rules(self, rules_manager):
        rules_manager.upsert_rule("TRADER JOES", "Chase Sapphire")
        rules_manager.upsert_rule("TRADER JOES", "Amex Gold")
        assert len(rules_manager.list_rules()) == 2


# ── get_rule ──────────────────────────────────────────────────────────────────

class TestGetRule:
    def test_returns_matching_rule(self, rules_manager):
        rules_manager.upsert_rule("LYFT", "Chase Freedom", primary_category="Transportation")
        rule = rules_manager.get_rule("LYFT", "Chase Freedom")
        assert rule is not None
        assert rule.primary_category == "Transportation"

    def test_returns_none_when_not_found(self, rules_manager):
        assert rules_manager.get_rule("NONEXISTENT", "SoFi") is None

    def test_returns_none_for_wrong_account_name(self, rules_manager):
        rules_manager.upsert_rule("LYFT", "Chase Freedom")
        assert rules_manager.get_rule("LYFT", "WRONG ACCOUNT") is None


# ── list_rules ────────────────────────────────────────────────────────────────

class TestListRules:
    def test_returns_empty_list_when_no_rules(self, rules_manager):
        assert rules_manager.list_rules() == []

    def test_returns_all_rules(self, rules_manager):
        rules_manager.upsert_rule("A", "Acct1")
        rules_manager.upsert_rule("B", "Acct2")
        rules_manager.upsert_rule("C", "Acct3")
        assert len(rules_manager.list_rules()) == 3


# ── update_rule ───────────────────────────────────────────────────────────────

class TestUpdateRule:
    def test_patches_specified_fields_only(self, rules_manager):
        rule = rules_manager.upsert_rule(
            "WHOLE FOODS", "Chase Sapphire", primary_category="Food & drink"
        )
        updated = rules_manager.update_rule(rule.id, detailed_category="Groceries")
        assert updated.primary_category == "Food & drink"  # untouched
        assert updated.detailed_category == "Groceries"

    def test_auto_sets_updated_at(self, rules_manager):
        before = datetime.now()
        rule = rules_manager.upsert_rule("CVS", "Chase Freedom")
        updated = rules_manager.update_rule(rule.id, primary_category="Health & wellness")
        assert updated.updated_at >= before

    def test_tags_list_coerced_to_string(self, rules_manager):
        rule = rules_manager.upsert_rule("SPOTIFY", "SoFi Checking")
        updated = rules_manager.update_rule(rule.id, tags=["music", "subscription"])
        assert updated.tags == "music,subscription"

    def test_tags_empty_list_stores_none(self, rules_manager):
        rule = rules_manager.upsert_rule("SPOTIFY", "SoFi Checking", tags=["music"])
        updated = rules_manager.update_rule(rule.id, tags=[])
        assert updated.tags is None


# ── delete_rule ───────────────────────────────────────────────────────────────

class TestDeleteRule:
    def test_removes_rule(self, rules_manager):
        rule = rules_manager.upsert_rule("PARKING", "Chase Freedom")
        rules_manager.delete_rule(rule.id)
        assert rules_manager.get_rule("PARKING", "Chase Freedom") is None

    def test_other_rules_unaffected(self, rules_manager):
        r1 = rules_manager.upsert_rule("A", "Acct")
        r2 = rules_manager.upsert_rule("B", "Acct")
        rules_manager.delete_rule(r1.id)
        remaining = rules_manager.list_rules()
        assert len(remaining) == 1
        assert remaining[0].id == r2.id


# ── stubs ─────────────────────────────────────────────────────────────────────

class TestStubs:
    def test_apply_rules_to_transaction_does_not_raise(self, rules_manager):
        rules_manager.apply_rules_to_transaction(transaction_id=42)

    def test_apply_rules_to_all_does_not_raise(self, rules_manager):
        rules_manager.apply_rules_to_all()
