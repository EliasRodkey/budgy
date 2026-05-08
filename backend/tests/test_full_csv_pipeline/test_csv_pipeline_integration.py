#!python3
"""
Full CSV upload pipeline integration test suite.

Runs real AI calls against 8 fixture CSVs covering major bank formats and adversarial
edge cases. Tests each pipeline stage independently with early exit on fatal errors.

Per-run detail is written to results/runs/<timestamp>.json; headline scores are
appended to results/results.csv. Pass --run-description to label the run.
Pytest only fails on fatal pipeline errors (exceptions, job failure, unexpected
unmapped required columns).

Run with:
    pytest backend/tests/test_full_csv_pipeline/ -m ai_integration -v -s \\
      --run-description "what changed"
"""
import csv as csv_lib
import io
import json
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from backend.ai_modules.csv_normalization_service.csv_normalization_service import CSVNormalizationService
from backend.ai_modules.csv_normalization_service.csv_normalization_planner import CSVNormalizationPlanner
from backend.ai_modules.csv_normalization_service.csv_transform_applicator import apply_normalization_plan
from backend.ai_modules.csv_normalization_service.normalization_plan import NormalizationPlan
from backend.api.ai.ai_router import _extract_candidate_categories, _extract_sample_amounts
from backend.api.transactions.transactions_router import _process_csv_upload
from backend.csv_modules.csv_parser import detect_delimiter, unwrap_row_quotes
from backend.tests.test_full_csv_pipeline.scorer import score_plan, score_rows
from backend.tests.test_full_csv_pipeline.results_writer import write_results

FIXTURES_DIR = Path(__file__).parent / "fixtures"

FIXTURE_NAMES = [
    "sofi_happy_path",
    "chase",
    "apple_card",
    "mint",
    "adversarial_delimiter",
    "adversarial_personal",
    "adversarial_structural",
    "adversarial_encoding",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_fixture(name: str) -> tuple[Path, dict]:
    csv_path = FIXTURES_DIR / f"{name}.csv"
    expected_path = FIXTURES_DIR / f"{name}.expected.json"
    with open(expected_path) as f:
        sidecar = json.load(f)
    return csv_path, sidecar


def _make_session_mock() -> MagicMock:
    session = MagicMock()
    session.category_mapping_rules.get_column_rule.return_value = None
    session.category_mapping_rules.get_category_rule.return_value = None
    session.transactions.count_items.return_value = 0
    session.transactions.upload_csv.return_value = []
    session.transactions.to_dataframe.return_value = __import__("pandas").DataFrame()
    return session


def _skip_remaining(result: dict, stage_names: list[str]) -> None:
    for name in stage_names:
        result["stages"][name] = {"status": "skipped"}


# ── Test ──────────────────────────────────────────────────────────────────────

@pytest.mark.ai_integration
@pytest.mark.parametrize("fixture_name", FIXTURE_NAMES)
def test_csv_pipeline(fixture_name: str, tmp_path: Path, run_context: dict) -> None:
    csv_path, sidecar = _load_fixture(fixture_name)

    result: dict = {
        "description": sidecar.get("description", ""),
        "stages": {},
        "overall_score": None,
    }

    plan: Optional[NormalizationPlan] = None
    raw_rows: list[dict] = []
    headers: list[str] = []

    # ── Stage 1: CSV Parsing ──────────────────────────────────────────────────
    try:
        raw_text = csv_path.read_text(encoding="utf-8", errors="replace")
        unwrapped = unwrap_row_quotes(raw_text)
        delimiter_detected = detect_delimiter(unwrapped)
        reader = csv_lib.DictReader(io.StringIO(unwrapped), delimiter=delimiter_detected)
        raw_rows = list(reader)
        headers = list(raw_rows[0].keys()) if raw_rows else []

        if not raw_rows:
            result["stages"]["csv_parsing"] = {
                "status": "fatal",
                "delimiter_detected": delimiter_detected,
                "row_count": 0,
                "errors": ["No rows parsed from CSV"],
            }
            write_results(fixture_name, result, run_context)
            pytest.fail(f"[{fixture_name}] csv_parsing: no rows parsed")

        result["stages"]["csv_parsing"] = {
            "status": "pass",
            "delimiter_detected": delimiter_detected,
            "row_count": len(raw_rows),
            "headers": headers,
            "errors": [],
        }
    except Exception as exc:
        result["stages"]["csv_parsing"] = {"status": "fatal", "errors": [str(exc)]}
        _skip_remaining(result, ["ai_planning", "plan_validation",
                                  "transform_application", "database_upload"])
        write_results(fixture_name, result, run_context)
        pytest.fail(f"[{fixture_name}] csv_parsing raised: {exc}")

    # ── Stage 2: AI Planning ──────────────────────────────────────────────────
    try:
        unique_categories = _extract_candidate_categories(raw_rows, headers)
        sample_amounts = _extract_sample_amounts(raw_rows, headers)

        rules_mock = MagicMock()
        rules_mock.get_column_rule.return_value = None
        rules_mock.get_category_rule.return_value = None

        ai_service = CSVNormalizationService()
        planner = CSVNormalizationPlanner(rules_manager=rules_mock, ai_service=ai_service)
        plan, used_cache = planner.plan(headers, unique_categories,
                                        sample_amount_values=sample_amounts)

        plan_score = score_plan(plan, sidecar)

        result["stages"]["ai_planning"] = {
            "status": "pass",
            "used_cache": used_cache,
            "plan_score": plan_score,
            "plan": {
                "column_map": plan.column_map,
                "category_map": {
                    k: {"primary": v.primary, "detailed": v.detailed}
                    for k, v in plan.category_map.items()
                },
                "amount_transform": plan.amount_transform.value,
                "debit_column": plan.debit_column,
                "credit_column": plan.credit_column,
                "unmapped_required_columns": plan.unmapped_required_columns,
                "issues": plan.issues,
                "column_map_reasoning": plan.column_map_reasoning,
                "category_map_reasoning": plan.category_map_reasoning,
                "amount_transform_reasoning": plan.amount_transform_reasoning,
            },
            "errors": [],
        }
    except Exception as exc:
        result["stages"]["ai_planning"] = {"status": "fatal", "errors": [str(exc)]}
        _skip_remaining(result, ["plan_validation", "transform_application", "database_upload"])
        write_results(fixture_name, result, run_context)
        pytest.fail(f"[{fixture_name}] ai_planning raised: {exc}")

    # ── Stage 3: Plan Validation ──────────────────────────────────────────────
    expected_unmapped = sidecar.get("expected_unmapped_required_columns", [])
    unexpected_unmapped = [
        c for c in plan.unmapped_required_columns if c not in expected_unmapped
    ]

    validation_status = "fatal" if unexpected_unmapped else "pass"
    result["stages"]["plan_validation"] = {
        "status": validation_status,
        "unmapped_required_columns": plan.unmapped_required_columns,
        "expected_unmapped": expected_unmapped,
        "errors": (
            [f"Unexpected unmapped required columns: {unexpected_unmapped}"]
            if unexpected_unmapped else []
        ),
    }

    if unexpected_unmapped:
        _skip_remaining(result, ["transform_application", "database_upload"])
        write_results(fixture_name, result, run_context)
        pytest.fail(
            f"[{fixture_name}] plan_validation: unexpected unmapped required columns: "
            f"{unexpected_unmapped}"
        )

    # ── Stage 4: Transform Application ───────────────────────────────────────
    try:
        transformed_rows, skipped_rows = apply_normalization_plan(raw_rows, plan)
        soft_fail_count = sum(
            1 for r in transformed_rows if r.get("status") == "Unchecked"
        )
        row_score = score_rows(transformed_rows, sidecar.get("expected_rows", []))

        result["stages"]["transform_application"] = {
            "status": "pass",
            "row_score": row_score,
            "skipped_rows": skipped_rows,
            "skipped_row_count": len(skipped_rows),
            "soft_fail_count": soft_fail_count,
            "errors": [],
        }
    except Exception as exc:
        result["stages"]["transform_application"] = {"status": "fatal", "errors": [str(exc)]}
        _skip_remaining(result, ["database_upload"])
        write_results(fixture_name, result, run_context)
        pytest.fail(f"[{fixture_name}] transform_application raised: {exc}")

    # ── Stage 5: Database Upload ──────────────────────────────────────────────
    try:
        csv_tmp = tmp_path / f"{fixture_name}.csv"
        csv_tmp.write_bytes(csv_path.read_bytes())
        session = _make_session_mock()

        with patch("backend.api.transactions.transactions_router.DatabaseSession") as MockSession, \
             patch("backend.api.transactions.transactions_router.DatabaseFile"):
            MockSession.return_value = session
            _process_csv_upload("test-job-id", str(csv_tmp), plan.model_dump_json())

        status_calls = {c[0][1]: c for c in session.jobs.set_status.call_args_list}
        final_status = "complete" if "complete" in status_calls else "failed"

        if final_status == "failed":
            error_msg = status_calls["failed"][1].get("errors", "unknown error")
            result["stages"]["database_upload"] = {
                "status": "fatal",
                "errors": [str(error_msg)],
            }
            write_results(fixture_name, result, run_context)
            pytest.fail(f"[{fixture_name}] database_upload job failed: {error_msg}")

        complete_kwargs = status_calls["complete"][1]
        result["stages"]["database_upload"] = {
            "status": "pass",
            "rows_imported": complete_kwargs.get("rows_imported", 0),
            "rows_updated": complete_kwargs.get("rows_updated", 0),
            "rows_skipped": complete_kwargs.get("rows_skipped", 0),
            "new_rules_saved": complete_kwargs.get("new_rules_saved", 0),
            "errors": [],
        }
    except Exception as exc:
        result["stages"]["database_upload"] = {"status": "fatal", "errors": [str(exc)]}
        write_results(fixture_name, result, run_context)
        pytest.fail(f"[{fixture_name}] database_upload raised: {exc}")

    # ── Overall Score ─────────────────────────────────────────────────────────
    plan_stage = result["stages"]["ai_planning"]
    transform_stage = result["stages"]["transform_application"]

    col_score = plan_stage["plan_score"]["column_map"]["score"]
    cat_score = plan_stage["plan_score"]["category_map"]["score"]
    transform_score = plan_stage["plan_score"]["amount_transform"]["score"]
    row_score_val = transform_stage["row_score"]["score"]

    result["overall_score"] = round(
        (col_score + cat_score + transform_score + row_score_val) / 4, 4
    )

    write_results(fixture_name, result, run_context)
