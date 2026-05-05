#!python3
"""
Diagnostic integration tests for the CSV upload pipeline using Gia Transactions.csv.

Tests each stage of the pipeline to pinpoint bugs that produce the generic
"Something went wrong processing your file" message in the UI.

Stages tested:
  1. apply_normalization_plan — unit-level transform of raw Gia rows
  2. _process_csv_upload      — full background-task integration with a temp DB
"""
import csv
import io
import os
import tempfile
from unittest.mock import patch

import pytest

from backend.ai_modules.csv_normalization_service.csv_transform_applicator import apply_normalization_plan
from backend.ai_modules.csv_normalization_service.normalization_plan import AmountTransform, CategoryMapping, NormalizationPlan
from backend.api.transactions.transactions_router import _process_csv_upload
from backend.csv_modules.csv_parser import unwrap_row_quotes
from backend.database_modules.db_session import DatabaseSession
from backend.database_modules.models.common import parse_date
from pleasant_database import DatabaseFile

GIA_CSV_PATH = os.path.join(os.getcwd(), "data", "csv_downloads", "Gia Transactions.csv")


def _make_gia_plan() -> NormalizationPlan:
    """NormalizationPlan for Gia Transactions.csv with Date→authorized_date (custom transform)."""
    return NormalizationPlan(
        column_map={
            "Date": "authorized_date",
            "Item": "description",
            "Category": "primary_category",
            "MOP": "account_name",
            "Cost": "amount",
        },
        category_map={
            "Bolt": CategoryMapping(primary="Transportation", detailed="Rideshare"),
            "Metro": CategoryMapping(primary="Transportation", detailed="Public Transit"),
            "Restaurants": CategoryMapping(primary="Food & Drink", detailed="Restaurants & Bars"),
            "Bars": CategoryMapping(primary="Food & Drink", detailed="Bars"),
            "Shopping": CategoryMapping(primary="Shopping", detailed="General"),
            "Groceries": CategoryMapping(primary="Food & Drink", detailed="Groceries"),
            "Entertainment": CategoryMapping(primary="Entertainment", detailed="General"),
            "WiFi + Phone": CategoryMapping(primary="Utilities", detailed="Phone & Internet"),
            "Health + Hygiene + Fitness": CategoryMapping(primary="Health", detailed="General"),
        },
        amount_transform=AmountTransform.INVERT,
        unmapped_required_columns=[],
    )


def _read_gia_rows() -> list[dict[str, str]]:
    """Read and unwrap the Gia CSV, returning a list of raw row dicts."""
    with open(GIA_CSV_PATH, encoding="utf-8") as f:
        text = f.read()
    text = unwrap_row_quotes(text)
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


# ── Stage 1: apply_normalization_plan ────────────────────────────────────────

class TestApplyNormalizationPlanGia:
    """Unit tests for the transformation stage using real Gia CSV rows."""

    def test_no_rows_skipped(self):
        # Bug 1 fix: unwrap_row_quotes now unescapes "" → " so rows with
        # comma-in-amounts (e.g. "$1,298.23") parse correctly instead of being skipped.
        rows = _read_gia_rows()
        _, skipped = apply_normalization_plan(rows, _make_gia_plan())
        assert skipped == [], f"Unexpected skipped rows: {skipped}"

    def test_none_amount_rows_are_tolerated(self):
        # Row with a non-numeric cost ("14-Dec") produces amount=None after _parse_amount.
        # The pipeline must not crash on it; the row is imported with amount=None and
        # can be corrected later via the edit modal.
        rows = _read_gia_rows()
        transformed, _ = apply_normalization_plan(rows, _make_gia_plan())
        none_rows = [i for i, r in enumerate(transformed, 1) if r.get("amount") is None]
        # Exactly one row has a non-numeric cost in Gia's CSV ("14-Dec").
        assert len(none_rows) <= 1, (
            f"More None-amount rows than expected: row numbers {none_rows}"
        )

    def test_all_dates_parseable(self):
        rows = _read_gia_rows()
        transformed, _ = apply_normalization_plan(rows, _make_gia_plan())
        for i, row in enumerate(transformed, 1):
            date_val = row.get("authorized_date")
            assert date_val, f"Row {i}: missing authorized_date"
            try:
                parse_date(str(date_val))
            except ValueError as e:
                pytest.fail(f"Row {i}: unparseable date {date_val!r}: {e}")

    def test_expense_amounts_are_negative(self):
        """Positive costs in Gia CSV should be negated (INVERT transform → expenses < 0)."""
        rows = _read_gia_rows()
        transformed, _ = apply_normalization_plan(rows, _make_gia_plan())
        uber_rows = [r for r in transformed if r.get("description") == "Uber"]
        assert uber_rows, "Uber row not found in transformed output"
        assert uber_rows[0]["amount"] < 0, (
            f"Expected negative expense for Uber, got {uber_rows[0]['amount']}"
        )

    def test_row_count_matches_input(self):
        rows = _read_gia_rows()
        transformed, skipped = apply_normalization_plan(rows, _make_gia_plan())
        assert len(transformed) + len(skipped) == len(rows)

    def test_required_fields_present(self):
        rows = _read_gia_rows()
        transformed, _ = apply_normalization_plan(rows, _make_gia_plan())
        required = {"authorized_date", "description", "amount"}
        for i, row in enumerate(transformed, 1):
            for field in required:
                assert field in row, f"Row {i}: missing required field '{field}'"


# ── Stage 2: full _process_csv_upload integration ────────────────────────────

class TestFullPipelineGia:
    """Integration tests for the full background-task pipeline with a temp DB."""

    def test_process_csv_upload_succeeds(self):
        """
        Full pipeline end-to-end: Gia CSV → transform → write temp CSV → upload_csv → DB.
        If the job ends up in 'failed' state, the assertion prints job.errors — that's
        the real error behind the 'Something went wrong processing your file' UI message.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_db_file = DatabaseFile("test_gia.db", tmp_dir)

            # Write Gia CSV to a temp path (mirrors what import_transactions_csv does)
            csv_tmp = os.path.join(tmp_dir, "Gia_Transactions.csv")
            with open(GIA_CSV_PATH, "rb") as src, open(csv_tmp, "wb") as dst:
                dst.write(src.read())

            # Create the job record
            with DatabaseSession(test_db_file) as session:
                job_id = session.jobs.create_job(csv_tmp)

            plan_json = _make_gia_plan().model_dump_json()

            # Redirect DatabaseFile/DatabaseSession in the router to use the temp DB
            with patch("backend.api.transactions.transactions_router.DatabaseFile") as MockDBFile, \
                 patch("backend.api.transactions.transactions_router.DatabaseSession") as MockDBSession:
                MockDBFile.return_value = test_db_file
                MockDBSession.side_effect = lambda _db: DatabaseSession(test_db_file)

                _process_csv_upload(job_id, csv_tmp, plan_json)

            # Inspect the result — the temp CSV is deleted by _process_csv_upload
            with DatabaseSession(test_db_file) as session:
                job = session.jobs.get_job(job_id)
                rows_imported = job.rows_imported if job else None

        assert job is not None, "Job record not found after processing"
        assert job.status == "complete", (
            f"\n\nImport pipeline FAILED.\n"
            f"job.errors = {job.errors!r}\n\n"
            f"This is the real error behind the generic UI message."
        )
        assert rows_imported and rows_imported > 0, (
            f"No rows imported (rows_imported={rows_imported}). job.errors: {job.errors}"
        )

    def test_process_csv_upload_second_time_no_crash(self):
        """Re-importing the same CSV should update existing rows, not crash."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_db_file = DatabaseFile("test_gia_2.db", tmp_dir)

            plan_json = _make_gia_plan().model_dump_json()

            def run_import():
                csv_tmp = os.path.join(tmp_dir, f"Gia_{os.urandom(4).hex()}.csv")
                with open(GIA_CSV_PATH, "rb") as src, open(csv_tmp, "wb") as dst:
                    dst.write(src.read())
                with DatabaseSession(test_db_file) as session:
                    job_id = session.jobs.create_job(csv_tmp)
                with patch("backend.api.transactions.transactions_router.DatabaseFile") as MockDBFile, \
                     patch("backend.api.transactions.transactions_router.DatabaseSession") as MockDBSession:
                    MockDBFile.return_value = test_db_file
                    MockDBSession.side_effect = lambda _db: DatabaseSession(test_db_file)
                    _process_csv_upload(job_id, csv_tmp, plan_json)
                with DatabaseSession(test_db_file) as session:
                    return session.jobs.get_job(job_id)

            first = run_import()
            assert first.status == "complete", f"First import failed: {first.errors}"

            second = run_import()
            assert second.status == "complete", f"Second import failed: {second.errors}"
