#!python3
"""
Tests for the /rules API endpoints (issue #59).

Covers:
    - GET /rules: list rules
    - POST /rules: create a rule, conflict on duplicate (match_description, match_account_name)
    - PUT /rules/{id}: update a rule, 404 for missing, conflict on duplicate
    - DELETE /rules/{id}: delete a rule, 404 for missing
    - GET /rules/{id}/matches: matched transaction count + capped preview list
    - Retroactive application: creating/updating a rule re-applies it to matching
      transactions and marks affected months dirty
"""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from pleasant_database import DatabaseFile

from backend.database_modules.db_session import DatabaseSession
from backend.database_modules.managers.transaction_manager import TransactionsTableManager, UpdatesTableManager
from backend.main import app
from backend.api.rules import rules_router as rules_router_module
from backend.database_modules.models.transactions import TransactionsTable
from backend.tests.conftest import TEST_DB_DIR, TEST_DB_FILENAME, TEST_DB_FILEPATH


def _override_get_db():
    db_file = DatabaseFile(TEST_DB_FILEPATH, TEST_DB_DIR)
    session = DatabaseSession(db_file)
    try:
        yield session
    finally:
        session.close()


app.dependency_overrides[rules_router_module.get_db] = _override_get_db
client = TestClient(app)


@pytest.fixture()
def db_session():
    db_file = DatabaseFile(TEST_DB_FILEPATH, TEST_DB_DIR)
    session = DatabaseSession(db_file)
    yield session

    session.rules.clear_table()
    session.rules.end_session()
    session.dirty_months.clear_table()
    session.dirty_months.end_session()
    session.transactions.clear_table()
    session.updates.clear_table()
    session.updates.end_session()
    session.transactions.end_session()
    session.close()


@pytest.fixture()
def seeded_transactions(db_session):
    """Seeds two TRADER JOES transactions on Chase Sapphire and one unrelated transaction."""
    now = datetime(2024, 3, 15)
    db_session.transactions.add_item(
        authorized_date=now, posted_date=now, status="posted",
        account_name="Chase Sapphire", description="TRADER JOES",
        primary_category="Other", detailed_category="Other",
        amount=-42.50, repayment=False, exclude=False,
        base_hash="hash1", uq_hash="uq1",
    )
    db_session.transactions.add_item(
        authorized_date=now, posted_date=now, status="posted",
        account_name="Chase Sapphire", description="TRADER JOES",
        primary_category="Other", detailed_category="Other",
        amount=-18.00, repayment=False, exclude=False,
        base_hash="hash2", uq_hash="uq2",
    )
    db_session.transactions.add_item(
        authorized_date=now, posted_date=now, status="posted",
        account_name="SoFi Checking", description="NETFLIX",
        primary_category="Other", detailed_category="Other",
        amount=-15.99, repayment=False, exclude=False,
        base_hash="hash3", uq_hash="uq3",
    )
    return db_session


# ── GET /rules ─────────────────────────────────────────────────────────────────

class TestListRules:
    def test_empty_list(self, db_session):
        resp = client.get("/rules")
        assert resp.status_code == 200
        assert resp.json() == {"data": []}

    def test_returns_created_rules(self, db_session):
        db_session.rules.upsert_rule(
            match_description="TRADER JOES",
            match_account_name="Chase Sapphire",
            primary_category="Food & drink",
            detailed_category="Groceries",
        )
        resp = client.get("/rules")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["matchDescription"] == "TRADER JOES"
        assert data[0]["matchAccountName"] == "Chase Sapphire"
        assert data[0]["primaryCategory"] == "Food & drink"
        assert data[0]["detailedCategory"] == "Groceries"


# ── POST /rules ────────────────────────────────────────────────────────────────

class TestCreateRule:
    def test_creates_rule(self, db_session):
        resp = client.post("/rules", json={
            "matchDescription": "TRADER JOES",
            "matchAccountName": "Chase Sapphire",
            "primaryCategory": "Food & drink",
            "detailedCategory": "Groceries",
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["matchDescription"] == "TRADER JOES"
        assert body["matchAccountName"] == "Chase Sapphire"
        assert body["primaryCategory"] == "Food & drink"
        assert body["detailedCategory"] == "Groceries"
        assert body["id"] is not None

    def test_duplicate_returns_409(self, db_session):
        db_session.rules.upsert_rule(
            match_description="TRADER JOES",
            match_account_name="Chase Sapphire",
            primary_category="Food & drink",
        )
        resp = client.post("/rules", json={
            "matchDescription": "TRADER JOES",
            "matchAccountName": "Chase Sapphire",
            "primaryCategory": "Other",
        })
        assert resp.status_code == 409

    def test_create_applies_retroactively(self, seeded_transactions):
        db = seeded_transactions
        resp = client.post("/rules", json={
            "matchDescription": "TRADER JOES",
            "matchAccountName": "Chase Sapphire",
            "primaryCategory": "Food & drink",
            "detailedCategory": "Groceries",
        })
        assert resp.status_code == 201

        rows = db.transactions.query(
            columns=db.transactions.return_columns,
            filters={TransactionsTable.description.name: ("==", "TRADER JOES")},
        ).data.to_dict(orient="records")
        assert len(rows) == 2
        for row in rows:
            assert row[TransactionsTable.primary_category.name] == "Food & drink"
            assert row[TransactionsTable.detailed_category.name] == "Groceries"

        dirty = db.dirty_months.get_all_dirty()
        assert (3, 2024) in dirty


# ── PUT /rules/{id} ───────────────────────────────────────────────────────────

class TestUpdateRule:
    def test_updates_rule(self, db_session):
        rule = db_session.rules.upsert_rule(
            match_description="TRADER JOES",
            match_account_name="Chase Sapphire",
            primary_category="Food & drink",
            detailed_category="Groceries",
        )
        resp = client.put(f"/rules/{rule.id}", json={
            "matchDescription": "TRADER JOES",
            "matchAccountName": "Chase Sapphire",
            "primaryCategory": "Food & drink",
            "detailedCategory": "Restaurants & bars",
            "exclude": True,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["detailedCategory"] == "Restaurants & bars"
        assert body["exclude"] is True

    def test_update_applies_retroactively(self, seeded_transactions):
        db = seeded_transactions
        rule = db.rules.upsert_rule(
            match_description="TRADER JOES",
            match_account_name="Chase Sapphire",
            primary_category="Other",
            detailed_category="Other",
        )
        resp = client.put(f"/rules/{rule.id}", json={
            "matchDescription": "TRADER JOES",
            "matchAccountName": "Chase Sapphire",
            "primaryCategory": "Food & drink",
            "detailedCategory": "Groceries",
        })
        assert resp.status_code == 200

        rows = db.transactions.query(
            columns=db.transactions.return_columns,
            filters={TransactionsTable.description.name: ("==", "TRADER JOES")},
        ).data.to_dict(orient="records")
        for row in rows:
            assert row[TransactionsTable.primary_category.name] == "Food & drink"
            assert row[TransactionsTable.detailed_category.name] == "Groceries"

    def test_returns_404_for_missing_rule(self, db_session):
        resp = client.put("/rules/999999", json={
            "matchDescription": "TRADER JOES",
            "matchAccountName": "Chase Sapphire",
        })
        assert resp.status_code == 404

    def test_duplicate_returns_409(self, db_session):
        db_session.rules.upsert_rule(
            match_description="TRADER JOES",
            match_account_name="Chase Sapphire",
        )
        rule_b = db_session.rules.upsert_rule(
            match_description="NETFLIX",
            match_account_name="SoFi Checking",
        )
        resp = client.put(f"/rules/{rule_b.id}", json={
            "matchDescription": "TRADER JOES",
            "matchAccountName": "Chase Sapphire",
        })
        assert resp.status_code == 409


# ── DELETE /rules/{id} ────────────────────────────────────────────────────────

class TestDeleteRule:
    def test_deletes_rule(self, db_session):
        rule = db_session.rules.upsert_rule(
            match_description="TRADER JOES",
            match_account_name="Chase Sapphire",
            primary_category="Food & drink",
        )
        resp = client.delete(f"/rules/{rule.id}")
        assert resp.status_code == 204
        assert db_session.rules.list_rules() == []

    def test_returns_404_for_missing_rule(self, db_session):
        resp = client.delete("/rules/999999")
        assert resp.status_code == 404


# ── GET /rules/{id}/matches ───────────────────────────────────────────────────

class TestRuleMatches:
    def test_returns_match_count_and_transactions(self, seeded_transactions):
        db = seeded_transactions
        rule = db.rules.upsert_rule(
            match_description="TRADER JOES",
            match_account_name="Chase Sapphire",
            primary_category="Food & drink",
        )
        resp = client.get(f"/rules/{rule.id}/matches")
        assert resp.status_code == 200
        body = resp.json()
        assert body["matchCount"] == 2
        assert len(body["transactions"]) == 2
        for tx in body["transactions"]:
            assert tx["description"] == "TRADER JOES"
            assert tx["accountName"] == "Chase Sapphire"

    def test_returns_empty_for_no_matches(self, seeded_transactions):
        db = seeded_transactions
        rule = db.rules.upsert_rule(
            match_description="NO MATCH HERE",
            match_account_name="Nowhere",
            primary_category="Other",
        )
        resp = client.get(f"/rules/{rule.id}/matches")
        assert resp.status_code == 200
        body = resp.json()
        assert body["matchCount"] == 0
        assert body["transactions"] == []

    def test_returns_404_for_missing_rule(self, db_session):
        resp = client.get("/rules/999999/matches")
        assert resp.status_code == 404
