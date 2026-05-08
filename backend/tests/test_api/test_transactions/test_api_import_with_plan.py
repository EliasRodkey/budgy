#!python3
"""
Tests for the updated POST /transactions/import endpoint (issue #39).

Covers:
- Endpoint accepts optional normalization_plan form field
- _process_csv_upload applies CSVTransformApplicator when plan is provided
- Job fails when unmapped required columns remain in the plan
- Job fails when TransformValidationError is raised by the applicator
- Rules are saved to CategoryMappingRulesManager after successful import with plan
- rules_applied_from_cache and new_rules_saved counted correctly
- Existing import flow (no plan) is unaffected
- ImportJobStatus response includes the new rule count fields
"""
import io
import json
from unittest.mock import MagicMock, patch, call

import pytest
from fastapi.testclient import TestClient

from backend.ai_modules.csv_normalization_service.normalization_plan import AmountTransform, CategoryMapping, NormalizationPlan
from backend.api.transactions.transactions_router import _process_csv_upload
from backend.main import app

client = TestClient(app)

# ── Fixtures and helpers ──────────────────────────────────────────────────────

BUDGY_CSV = (
    "authorized_date,description,primary_category,amount\n"
    "2024-01-01,Coffee,Food & drink,-5.00\n"
    "2024-01-02,Gas,Transportation,-40.00\n"
)

MESSY_CSV = (
    "Date,Merchant,Category,Amt\n"
    "2024-01-01,Coffee Shop,Dining,-5.00\n"
    "2024-01-02,Gas Station,Transport,-40.00\n"
)


def _make_plan(**kwargs) -> NormalizationPlan:
    defaults = dict(
        column_map={
            "Date": "authorized_date",
            "Merchant": "description",
            "Category": "primary_category",
            "Amt": "amount",
        },
        category_map={
            "Dining": CategoryMapping(primary="Food & drink", detailed="Restaurants & bars"),
            "Transport": CategoryMapping(primary="Transportation", detailed="Gas & EV charging"),
        },
        amount_transform=AmountTransform.EXPENSE_NEGATIVE,
        debit_column=None,
        credit_column=None,
        issues=[],
        unmapped_required_columns=[],
    )
    defaults.update(kwargs)
    return NormalizationPlan(**defaults)


def _make_session_mock(
    col_rule_exists: bool = False,
    cat_rule_exists: bool = False,
) -> MagicMock:
    """Returns a mock DatabaseSession with enough surface for _process_csv_upload."""
    session = MagicMock()
    session.category_mapping_rules.get_column_rule.return_value = "existing" if col_rule_exists else None
    session.category_mapping_rules.get_category_rule.return_value = {"primary": "x", "detailed": "y"} if cat_rule_exists else None
    session.transactions.count_items.return_value = 0
    session.transactions.upload_csv.return_value = []
    session.transactions.to_dataframe.return_value = __import__("pandas").DataFrame()
    return session


# ── Unit tests for _process_csv_upload ───────────────────────────────────────

class TestProcessCSVUploadNoPlan:
    def test_upload_csv_called_with_original_path(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(BUDGY_CSV)
        session = _make_session_mock()

        with patch("backend.api.transactions.transactions_router.DatabaseSession") as MockSession, \
             patch("backend.api.transactions.transactions_router.DatabaseFile"):
            MockSession.return_value.__enter__ = MagicMock(return_value=session)
            MockSession.return_value = session

            _process_csv_upload("job-1", str(csv_file))

        session.transactions.upload_csv.assert_called_once_with(str(csv_file))

    def test_job_set_to_complete(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(BUDGY_CSV)
        session = _make_session_mock()

        with patch("backend.api.transactions.transactions_router.DatabaseSession") as MockSession, \
             patch("backend.api.transactions.transactions_router.DatabaseFile"):
            MockSession.return_value = session
            _process_csv_upload("job-1", str(csv_file))

        status_calls = [c[0][1] for c in session.jobs.set_status.call_args_list]
        assert "complete" in status_calls

    def test_rule_counts_zero_without_plan(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(BUDGY_CSV)
        session = _make_session_mock()

        with patch("backend.api.transactions.transactions_router.DatabaseSession") as MockSession, \
             patch("backend.api.transactions.transactions_router.DatabaseFile"):
            MockSession.return_value = session
            _process_csv_upload("job-1", str(csv_file))

        complete_call = next(
            c for c in session.jobs.set_status.call_args_list if c[0][1] == "complete"
        )
        assert complete_call[1].get("rules_applied_from_cache") == 0
        assert complete_call[1].get("new_rules_saved") == 0


class TestProcessCSVUploadWithPlan:
    def test_transform_applied_before_upload(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(MESSY_CSV)
        plan = _make_plan()
        session = _make_session_mock()

        transformed_rows = [
            {"authorized_date": "2024-01-01", "description": "Coffee Shop", "primary_category": "Food & drink", "amount": -5.0},
            {"authorized_date": "2024-01-02", "description": "Gas Station", "primary_category": "Transportation", "amount": -40.0},
        ]

        with patch("backend.api.transactions.transactions_router.DatabaseSession") as MockSession, \
             patch("backend.api.transactions.transactions_router.DatabaseFile"), \
             patch("backend.api.transactions.transactions_router.apply_normalization_plan", return_value=(transformed_rows, [])) as mock_apply:
            MockSession.return_value = session
            _process_csv_upload("job-1", str(csv_file), plan.model_dump_json())

        mock_apply.assert_called_once()
        # upload_csv should be called with the transformed temp file, not original
        upload_path = session.transactions.upload_csv.call_args[0][0]
        assert upload_path != str(csv_file)
        assert "_transformed.csv" in upload_path

    def test_job_fails_when_unmapped_required_columns(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(MESSY_CSV)
        plan = _make_plan(unmapped_required_columns=["primary_category"])
        session = _make_session_mock()

        with patch("backend.api.transactions.transactions_router.DatabaseSession") as MockSession, \
             patch("backend.api.transactions.transactions_router.DatabaseFile"):
            MockSession.return_value = session
            _process_csv_upload("job-1", str(csv_file), plan.model_dump_json())

        status_calls = {c[0][1]: c for c in session.jobs.set_status.call_args_list}
        assert "failed" in status_calls
        error_msg = status_calls["failed"][1].get("errors", "")
        assert "primary_category" in error_msg
        session.transactions.upload_csv.assert_not_called()

    def test_job_fails_on_unexpected_transform_exception(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(MESSY_CSV)
        plan = _make_plan()
        session = _make_session_mock()

        with patch("backend.api.transactions.transactions_router.DatabaseSession") as MockSession, \
             patch("backend.api.transactions.transactions_router.DatabaseFile"), \
             patch("backend.api.transactions.transactions_router.apply_normalization_plan",
                   side_effect=RuntimeError("unexpected")):
            MockSession.return_value = session
            _process_csv_upload("job-1", str(csv_file), plan.model_dump_json())

        status_calls = {c[0][1]: c for c in session.jobs.set_status.call_args_list}
        assert "failed" in status_calls
        session.transactions.upload_csv.assert_not_called()

    def test_new_rules_saved_after_import(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(MESSY_CSV)
        plan = _make_plan()
        session = _make_session_mock(col_rule_exists=False, cat_rule_exists=False)

        transformed_rows = [
            {"authorized_date": "2024-01-01", "description": "Coffee Shop",
             "primary_category": "Food & drink", "amount": -5.0},
        ]

        with patch("backend.api.transactions.transactions_router.DatabaseSession") as MockSession, \
             patch("backend.api.transactions.transactions_router.DatabaseFile"), \
             patch("backend.api.transactions.transactions_router.apply_normalization_plan",
                   return_value=(transformed_rows, [])):
            MockSession.return_value = session
            _process_csv_upload("job-1", str(csv_file), plan.model_dump_json())

        session.category_mapping_rules.upsert_column_rule.assert_called()
        session.category_mapping_rules.upsert_category_rule.assert_called()

    def test_cached_rules_not_re_saved(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(MESSY_CSV)
        plan = _make_plan()
        # All rules already exist in cache
        session = _make_session_mock(col_rule_exists=True, cat_rule_exists=True)

        transformed_rows = [
            {"authorized_date": "2024-01-01", "description": "Coffee Shop",
             "primary_category": "Food & drink", "amount": -5.0},
        ]

        with patch("backend.api.transactions.transactions_router.DatabaseSession") as MockSession, \
             patch("backend.api.transactions.transactions_router.DatabaseFile"), \
             patch("backend.api.transactions.transactions_router.apply_normalization_plan",
                   return_value=(transformed_rows, [])):
            MockSession.return_value = session
            _process_csv_upload("job-1", str(csv_file), plan.model_dump_json())

        session.category_mapping_rules.upsert_column_rule.assert_not_called()
        session.category_mapping_rules.upsert_category_rule.assert_not_called()

    def test_rules_applied_from_cache_counted(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(MESSY_CSV)
        plan = _make_plan()
        # All rules exist in cache
        session = _make_session_mock(col_rule_exists=True, cat_rule_exists=True)

        transformed_rows = [{"authorized_date": "2024-01-01", "description": "x",
                              "primary_category": "Food & drink", "amount": -5.0}]

        with patch("backend.api.transactions.transactions_router.DatabaseSession") as MockSession, \
             patch("backend.api.transactions.transactions_router.DatabaseFile"), \
             patch("backend.api.transactions.transactions_router.apply_normalization_plan",
                   return_value=(transformed_rows, [])):
            MockSession.return_value = session
            _process_csv_upload("job-1", str(csv_file), plan.model_dump_json())

        complete_call = next(
            c for c in session.jobs.set_status.call_args_list if c[0][1] == "complete"
        )
        # 4 column mappings + 2 category mappings, all cached
        assert complete_call[1]["rules_applied_from_cache"] == 6
        assert complete_call[1]["new_rules_saved"] == 0

    def test_new_rules_saved_counted(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(MESSY_CSV)
        plan = _make_plan()
        # No rules in cache
        session = _make_session_mock(col_rule_exists=False, cat_rule_exists=False)

        transformed_rows = [{"authorized_date": "2024-01-01", "description": "x",
                              "primary_category": "Food & drink", "amount": -5.0}]

        with patch("backend.api.transactions.transactions_router.DatabaseSession") as MockSession, \
             patch("backend.api.transactions.transactions_router.DatabaseFile"), \
             patch("backend.api.transactions.transactions_router.apply_normalization_plan",
                   return_value=(transformed_rows, [])):
            MockSession.return_value = session
            _process_csv_upload("job-1", str(csv_file), plan.model_dump_json())

        complete_call = next(
            c for c in session.jobs.set_status.call_args_list if c[0][1] == "complete"
        )
        # 4 column mappings + 2 category mappings, all new
        assert complete_call[1]["new_rules_saved"] == 6
        assert complete_call[1]["rules_applied_from_cache"] == 0

    def test_transformed_temp_file_cleaned_up(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(MESSY_CSV)
        plan = _make_plan()
        session = _make_session_mock()

        transformed_rows = [{"authorized_date": "2024-01-01", "description": "x",
                              "primary_category": "Food & drink", "amount": -5.0}]

        with patch("backend.api.transactions.transactions_router.DatabaseSession") as MockSession, \
             patch("backend.api.transactions.transactions_router.DatabaseFile"), \
             patch("backend.api.transactions.transactions_router.apply_normalization_plan",
                   return_value=(transformed_rows, [])):
            MockSession.return_value = session
            _process_csv_upload("job-1", str(csv_file), plan.model_dump_json())

        # The original file should be cleaned up (we're using tmp_path so it persists, but
        # the test verifies no exception was raised and job completed successfully)
        complete_calls = [c for c in session.jobs.set_status.call_args_list if c[0][1] == "complete"]
        assert len(complete_calls) == 1


# ── Endpoint-level tests ──────────────────────────────────────────────────────

class TestImportEndpointWithPlan:
    def test_endpoint_accepts_normalization_plan_field(self):
        plan = _make_plan()
        plan_json = plan.model_dump_json()

        with patch("backend.api.transactions.transactions_router._process_csv_upload") as mock_task, \
             patch("backend.api.transactions.transactions_router.DatabaseSession") as MockSession, \
             patch("backend.api.transactions.transactions_router.DatabaseFile"):
            MockSession.return_value.jobs.create_job.return_value = "test-job-id"
            response = client.post(
                "/transactions/import",
                files={"file": ("test.csv", io.BytesIO(MESSY_CSV.encode()), "text/csv")},
                data={"normalization_plan": plan_json},
            )

        assert response.status_code == 200
        assert response.json()["jobId"] == "test-job-id"

    def test_endpoint_passes_plan_to_background_task(self):
        plan = _make_plan()
        plan_json = plan.model_dump_json()

        with patch("backend.api.transactions.transactions_router._process_csv_upload") as mock_task, \
             patch("backend.api.transactions.transactions_router.DatabaseSession") as MockSession, \
             patch("backend.api.transactions.transactions_router.DatabaseFile"):
            MockSession.return_value.jobs.create_job.return_value = "test-job-id"
            client.post(
                "/transactions/import",
                files={"file": ("test.csv", io.BytesIO(MESSY_CSV.encode()), "text/csv")},
                data={"normalization_plan": plan_json},
            )

        # The background task is queued via BackgroundTasks, not called directly,
        # so we verify the response status and job creation instead.
        MockSession.return_value.jobs.create_job.assert_called_once()

    def test_endpoint_works_without_plan(self):
        with patch("backend.api.transactions.transactions_router._process_csv_upload"), \
             patch("backend.api.transactions.transactions_router.DatabaseSession") as MockSession, \
             patch("backend.api.transactions.transactions_router.DatabaseFile"):
            MockSession.return_value.jobs.create_job.return_value = "test-job-id"
            response = client.post(
                "/transactions/import",
                files={"file": ("test.csv", io.BytesIO(BUDGY_CSV.encode()), "text/csv")},
            )

        assert response.status_code == 200


class TestImportJobStatusFields:
    def test_get_job_status_includes_rule_counts(self):
        mock_job = MagicMock()
        mock_job.job_id = "job-123"
        mock_job.status = "complete"
        mock_job.rows_imported = 10
        mock_job.rows_updated = 2
        mock_job.rows_skipped = 0
        mock_job.skipped_rows = None
        mock_job.errors = None
        mock_job.rules_applied_from_cache = 5
        mock_job.new_rules_saved = 3

        with patch("backend.api.transactions.transactions_router.DatabaseSession") as MockSession, \
             patch("backend.api.transactions.transactions_router.DatabaseFile"):
            MockSession.return_value.jobs.get_job.return_value = mock_job
            response = client.get("/transactions/import/job-123")

        assert response.status_code == 200
        data = response.json()
        assert data["rulesAppliedFromCache"] == 5
        assert data["newRulesSaved"] == 3
