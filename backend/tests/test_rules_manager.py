#!python3
"""
Tests for TransactionRulesManager.

Covers:
    - upsert_rule: create, update (idempotent upsert), exclude field
    - get_rule: found and not found
    - list_rules: empty and populated
    - update_rule: field patching, auto updated_at, list coercion
    - delete_rule: removes the record
    - apply_rules_to_transaction: applies matching rule to a single transaction
    - apply_rules_to_all: applies all rules to matching transactions, merges tags, applies exclude
"""
import pytest
from datetime import datetime

from pleasant_database import DatabaseFile
from backend.database_modules.managers.rules_manager import TransactionRulesManager
from backend.database_modules.managers.transaction_manager import TransactionsTableManager, UpdatesTableManager
from backend.tests.conftest import TEST_DB_DIR, TEST_DB_FILENAME, TEST_DB_FILEPATH


@pytest.fixture()
def rules_manager():
    """Fresh RulesManager backed by the shared test DB; table cleared after each test."""
    db_file = DatabaseFile(TEST_DB_FILEPATH, TEST_DB_DIR)
    manager = TransactionRulesManager(db_file)
    yield manager
    manager.clear_table()
    manager.end_session()


@pytest.fixture()
def tx_and_rules():
    """
    Provides a TransactionsTableManager and a TransactionRulesManager sharing the test DB.
    Seeds two transactions and tears down both tables after each test.
    """
    db_file = DatabaseFile(TEST_DB_FILEPATH, TEST_DB_DIR)
    updates_mgr = UpdatesTableManager(db_file)
    tx_mgr = TransactionsTableManager(db_file, updates_mgr)
    rules_mgr = TransactionRulesManager(db_file)

    now = datetime(2024, 3, 15)
    tx_mgr.add_item(
        authorized_date=now, posted_date=now, status="posted",
        account_name="Chase Sapphire", description="TRADER JOES",
        primary_category="Other", detailed_category="Other",
        amount=-42.50, repayment=False, exclude=False,
        base_hash="hash1", uq_hash="uq1",
    )
    tx_mgr.add_item(
        authorized_date=now, posted_date=now, status="posted",
        account_name="Chase Sapphire", description="TRADER JOES",
        primary_category="Other", detailed_category="Other",
        amount=-18.00, repayment=False, exclude=False,
        base_hash="hash2", uq_hash="uq2",
    )
    tx_mgr.add_item(
        authorized_date=now, posted_date=now, status="posted",
        account_name="SoFi Checking", description="NETFLIX",
        primary_category="Other", detailed_category="Other",
        amount=-15.99, repayment=False, exclude=False,
        base_hash="hash3", uq_hash="uq3",
    )

    yield tx_mgr, rules_mgr

    rules_mgr.clear_table()
    rules_mgr.end_session()
    tx_mgr.clear_table()
    updates_mgr.clear_table()
    updates_mgr.end_session()
    tx_mgr.end_session()


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

    def test_exclude_stored_and_retrieved(self, rules_manager):
        rule = rules_manager.upsert_rule("VENMO PAYMENT", "SoFi Checking", exclude=True)
        assert rule.exclude is True

    def test_exclude_false_stored(self, rules_manager):
        rule = rules_manager.upsert_rule("VENMO PAYMENT", "SoFi Checking", exclude=False)
        assert rule.exclude is False

    def test_exclude_updated_on_upsert(self, rules_manager):
        rules_manager.upsert_rule("VENMO PAYMENT", "SoFi Checking", exclude=False)
        updated = rules_manager.upsert_rule("VENMO PAYMENT", "SoFi Checking", exclude=True)
        assert updated.exclude is True


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


# ── apply_rules_to_transaction ────────────────────────────────────────────────

class TestApplyRulesToTransaction:
    def test_applies_category_from_matching_rule(self, tx_and_rules):
        tx_mgr, rules_mgr = tx_and_rules
        rows = tx_mgr.query(columns=tx_mgr.return_columns, filters={"description": ("==", "TRADER JOES")}).data
        tx_id = int(rows.iloc[0]["id"])

        rules_mgr.upsert_rule("TRADER JOES", "Chase Sapphire", primary_category="Food & drink", detailed_category="Groceries")
        changed = rules_mgr.apply_rules_to_transaction(tx_id, tx_mgr)

        assert changed is True
        updated = tx_mgr.query(columns=tx_mgr.return_columns, filters={"id": ("==", tx_id)}).data.iloc[0]
        assert updated["primary_category"] == "Food & drink"
        assert updated["detailed_category"] == "Groceries"

    def test_merges_tags_from_rule(self, tx_and_rules):
        tx_mgr, rules_mgr = tx_and_rules
        rows = tx_mgr.query(columns=tx_mgr.return_columns, filters={"description": ("==", "TRADER JOES")}).data
        tx_id = int(rows.iloc[0]["id"])
        tx_mgr.update_item(tx_id, tags="existing")

        rules_mgr.upsert_rule("TRADER JOES", "Chase Sapphire", tags=["groceries"])
        rules_mgr.apply_rules_to_transaction(tx_id, tx_mgr)

        updated = tx_mgr.query(columns=tx_mgr.return_columns, filters={"id": ("==", tx_id)}).data.iloc[0]
        tags = updated["tags"].split(",")
        assert "existing" in tags
        assert "groceries" in tags

    def test_applies_exclude_from_rule(self, tx_and_rules):
        tx_mgr, rules_mgr = tx_and_rules
        rows = tx_mgr.query(columns=tx_mgr.return_columns, filters={"description": ("==", "TRADER JOES")}).data
        tx_id = int(rows.iloc[0]["id"])

        rules_mgr.upsert_rule("TRADER JOES", "Chase Sapphire", exclude=True)
        rules_mgr.apply_rules_to_transaction(tx_id, tx_mgr)

        updated = tx_mgr.query(columns=tx_mgr.return_columns, filters={"id": ("==", tx_id)}).data.iloc[0]
        assert updated["exclude"] == True  # noqa: E712 — pandas returns np.True_, not Python True

    def test_returns_false_when_no_rule_matches(self, tx_and_rules):
        tx_mgr, rules_mgr = tx_and_rules
        rows = tx_mgr.query(columns=tx_mgr.return_columns, filters={"description": ("==", "TRADER JOES")}).data
        tx_id = int(rows.iloc[0]["id"])

        changed = rules_mgr.apply_rules_to_transaction(tx_id, tx_mgr)
        assert changed is False

    def test_returns_false_when_only_tags_change(self, tx_and_rules):
        tx_mgr, rules_mgr = tx_and_rules
        rows = tx_mgr.query(columns=tx_mgr.return_columns, filters={"description": ("==", "TRADER JOES")}).data
        tx_id = int(rows.iloc[0]["id"])

        rules_mgr.upsert_rule("TRADER JOES", "Chase Sapphire", tags=["groceries"])
        changed = rules_mgr.apply_rules_to_transaction(tx_id, tx_mgr)
        assert changed is False


# ── apply_rules_to_all ────────────────────────────────────────────────────────

class TestApplyRulesToAll:
    def test_updates_category_on_matching_transactions(self, tx_and_rules):
        tx_mgr, rules_mgr = tx_and_rules
        rules_mgr.upsert_rule("TRADER JOES", "Chase Sapphire", primary_category="Food & drink")
        rules_mgr.apply_rules_to_all(tx_mgr)

        rows = tx_mgr.query(columns=tx_mgr.return_columns, filters={"description": ("==", "TRADER JOES")}).data
        assert all(r == "Food & drink" for r in rows["primary_category"])

    def test_merges_tags_without_overwriting_existing(self, tx_and_rules):
        tx_mgr, rules_mgr = tx_and_rules
        rows = tx_mgr.query(columns=tx_mgr.return_columns, filters={"description": ("==", "TRADER JOES")}).data
        tx_mgr.update_item(int(rows.iloc[0]["id"]), tags="existing")

        rules_mgr.upsert_rule("TRADER JOES", "Chase Sapphire", tags=["groceries"])
        rules_mgr.apply_rules_to_all(tx_mgr)

        updated_row = tx_mgr.query(
            columns=tx_mgr.return_columns,
            filters={"id": ("==", int(rows.iloc[0]["id"]))}
        ).data.iloc[0]
        tags = updated_row["tags"].split(",")
        assert "existing" in tags
        assert "groceries" in tags

    def test_applies_exclude_from_rule(self, tx_and_rules):
        tx_mgr, rules_mgr = tx_and_rules
        rules_mgr.upsert_rule("TRADER JOES", "Chase Sapphire", exclude=True)
        rules_mgr.apply_rules_to_all(tx_mgr)

        rows = tx_mgr.query(columns=tx_mgr.return_columns, filters={"description": ("==", "TRADER JOES")}).data
        assert all(r == True for r in rows["exclude"])  # noqa: E712 — pandas returns np.True_

    def test_does_not_modify_non_matching_transactions(self, tx_and_rules):
        tx_mgr, rules_mgr = tx_and_rules
        rules_mgr.upsert_rule("TRADER JOES", "Chase Sapphire", primary_category="Food & drink")
        rules_mgr.apply_rules_to_all(tx_mgr)

        netflix_row = tx_mgr.query(
            columns=tx_mgr.return_columns, filters={"description": ("==", "NETFLIX")}
        ).data.iloc[0]
        assert netflix_row["primary_category"] == "Other"

    def test_idempotent(self, tx_and_rules):
        tx_mgr, rules_mgr = tx_and_rules
        rules_mgr.upsert_rule("TRADER JOES", "Chase Sapphire", primary_category="Food & drink", tags=["groceries"])

        rules_mgr.apply_rules_to_all(tx_mgr)
        rules_mgr.apply_rules_to_all(tx_mgr)

        rows = tx_mgr.query(columns=tx_mgr.return_columns, filters={"description": ("==", "TRADER JOES")}).data
        for _, row in rows.iterrows():
            tags = [t for t in (row["tags"] or "").split(",") if t]
            assert tags.count("groceries") == 1

    def test_returns_empty_list_when_no_rules(self, tx_and_rules):
        tx_mgr, rules_mgr = tx_and_rules
        result = rules_mgr.apply_rules_to_all(tx_mgr)
        assert result == []
