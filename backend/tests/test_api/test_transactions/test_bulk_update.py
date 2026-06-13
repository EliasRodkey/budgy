#!python3
"""
Tests for POST /transactions/bulk-update, focused on the save_as_rule flow
when a single transaction (no other matching transactions) is updated.

Covers:
    - save_as_rule=true with a single transaction id creates a rule when
      none exists for the (description, account_name) pair.
    - save_as_rule=true on a subsequent call updates (upserts) the existing
      rule rather than erroring.
"""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from pleasant_database import DatabaseFile

from backend.database_modules.db_session import DatabaseSession
from backend.main import app
from backend.api.transactions import transactions_router as transactions_router_module
from backend.database_modules.models.transactions import TransactionsTable
from backend.tests.conftest import TEST_DB_DIR, TEST_DB_FILENAME, TEST_DB_FILEPATH


def _override_get_db():
    db_file = DatabaseFile(TEST_DB_FILEPATH, TEST_DB_DIR)
    session = DatabaseSession(db_file)
    try:
        yield session
    finally:
        session.close()


app.dependency_overrides[transactions_router_module.get_db] = _override_get_db
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
def unique_transaction(db_session):
    """A single transaction with no other transactions sharing its (description, account_name)."""
    now = datetime(2024, 3, 15)
    db_session.transactions.add_item(
        authorized_date=now, posted_date=now, status="posted",
        account_name="Chase Sapphire", description="ACME WIDGET CO",
        primary_category="Other", detailed_category="Other",
        amount=-12.34, repayment=False, exclude=False,
        base_hash="hash1", uq_hash="uq1",
    )
    rows = db_session.transactions.query(
        columns=db_session.transactions.return_columns,
        filters={TransactionsTable.description.name: ("==", "ACME WIDGET CO")},
    ).data.to_dict(orient="records")
    return db_session, rows[0]["id"]


class TestBulkUpdateSaveAsRule:
    def test_creates_rule_for_single_transaction_with_no_similar(self, unique_transaction):
        db, tx_id = unique_transaction

        resp = client.post("/transactions/bulk-update", json={
            "transaction_ids": [tx_id],
            "primary_category": "Shopping",
            "detailed_category": "Online shopping",
            "save_as_rule": True,
            "match_description": "ACME WIDGET CO",
            "match_account_name": "Chase Sapphire",
        })
        assert resp.status_code == 200
        assert resp.json() == {"updated": 1}

        rule = db.rules.get_rule("ACME WIDGET CO", "Chase Sapphire")
        assert rule is not None
        assert rule.primary_category == "Shopping"
        assert rule.detailed_category == "Online shopping"

        row = db.transactions.fetch_item_by_id(tx_id)
        assert row.primary_category == "Shopping"
        assert row.detailed_category == "Online shopping"

    def test_save_as_rule_updates_existing_rule(self, unique_transaction):
        db, tx_id = unique_transaction
        db.rules.upsert_rule(
            match_description="ACME WIDGET CO",
            match_account_name="Chase Sapphire",
            primary_category="Shopping",
            detailed_category="Online shopping",
        )

        resp = client.post("/transactions/bulk-update", json={
            "transaction_ids": [tx_id],
            "primary_category": "Food & drink",
            "detailed_category": "Restaurants & bars",
            "save_as_rule": True,
            "match_description": "ACME WIDGET CO",
            "match_account_name": "Chase Sapphire",
        })
        assert resp.status_code == 200

        rules = db.rules.list_rules()
        assert len(rules) == 1
        assert rules[0].primary_category == "Food & drink"
        assert rules[0].detailed_category == "Restaurants & bars"
