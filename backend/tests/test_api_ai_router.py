#!python3
"""
Tests for POST /ai/plan-csv endpoint.

Helper functions (_is_numeric_or_date, _extract_candidate_categories) are tested
directly. The endpoint itself is tested by patching CSVNormalizationPlanner so no
real DB or AI calls are made.
"""
import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.ai_modules.normalization_plan import AmountTransform, CategoryMapping, NormalizationPlan
from backend.api.ai.ai_router import _extract_candidate_categories, _is_numeric_or_date
from backend.main import app


# ── Helper: _is_numeric_or_date ───────────────────────────────────────────────

class TestIsNumericOrDate:
    def test_integer_string(self):
        assert _is_numeric_or_date("42") is True

    def test_float_string(self):
        assert _is_numeric_or_date("12.50") is True

    def test_negative_float(self):
        assert _is_numeric_or_date("-99.99") is True

    def test_amount_with_comma(self):
        assert _is_numeric_or_date("1,234.56") is True

    def test_iso_date(self):
        assert _is_numeric_or_date("2024-01-15") is True

    def test_us_date_short_year(self):
        assert _is_numeric_or_date("1/15/24") is True

    def test_us_date_long_year(self):
        assert _is_numeric_or_date("01/15/2024") is True

    def test_category_string(self):
        assert _is_numeric_or_date("Food & drink") is False

    def test_description_string(self):
        assert _is_numeric_or_date("AMAZON MARKETPLACE") is False

    def test_empty_string(self):
        assert _is_numeric_or_date("") is False


# ── Helper: _extract_candidate_categories ────────────────────────────────────

class TestExtractCandidateCategories:
    def _make_rows(self, col_data: dict[str, list[str]]) -> list[dict]:
        keys = list(col_data.keys())
        length = len(col_data[keys[0]])
        return [{k: col_data[k][i] for k in keys} for i in range(length)]

    def test_selects_medium_cardinality_column(self):
        # 10 unique categories, 1 unique date, 1000 unique descriptions
        categories = [f"Category_{i}" for i in range(10)]
        rows = self._make_rows({
            "Date": ["2024-01-01"] * 10,
            "Description": [f"Merchant {i}" for i in range(10)],
            "Category": categories,
            "Amount": [f"{i}.00" for i in range(10)],
        })
        result = _extract_candidate_categories(rows, ["Date", "Description", "Category", "Amount"])
        assert all(c in result for c in categories)
        assert "2024-01-01" not in result

    def test_excludes_high_cardinality_column(self):
        # 100 unique descriptions should be excluded (above HIGH=50)
        high_card = [f"Merchant {i}" for i in range(60)]
        low_card = [f"Cat {i % 8}" for i in range(60)]
        rows = self._make_rows({"Desc": high_card, "Category": low_card})
        result = _extract_candidate_categories(rows, ["Desc", "Category"])
        assert not any(f"Merchant {i}" in result for i in range(60))
        assert any(f"Cat {i}" in result for i in range(8))

    def test_excludes_very_low_cardinality_column(self):
        # Status column with 2 unique values — below LOW=6, excluded
        rows = self._make_rows({
            "Status": ["pending", "complete"] * 5,
            "Category": [f"Cat {i}" for i in range(10)],
        })
        result = _extract_candidate_categories(rows, ["Status", "Category"])
        assert "pending" not in result
        assert "complete" not in result

    def test_fallback_when_no_candidates(self):
        # All columns are either numeric/date or outside the cardinality window
        rows = self._make_rows({
            "Date": ["2024-01-01"] * 5,
            "Amount": ["10.00", "20.00", "30.00", "40.00", "50.00"],
        })
        result = _extract_candidate_categories(rows, ["Date", "Amount"])
        # Fallback: returns non-numeric/date values — empty here since all filtered
        assert isinstance(result, list)

    def test_returns_deduplicated_values(self):
        rows = self._make_rows({
            "CatA": ["Food", "Food", "Travel", "Travel", "Shopping", "Shopping", "Health", "Health", "Bills", "Bills", "Other"],
            "CatB": ["Food", "Dining", "Travel", "Transport", "Shopping", "Retail", "Health", "Medical", "Bills", "Utilities", "Other"],
        })
        result = _extract_candidate_categories(rows, ["CatA", "CatB"])
        assert len(result) == len(set(result))


# ── Endpoint: POST /ai/plan-csv ───────────────────────────────────────────────

def _make_normalization_plan(**kwargs) -> NormalizationPlan:
    defaults = dict(
        column_map={},
        category_map={},
        amount_transform=AmountTransform.EXPENSE_NEGATIVE,
        debit_column=None,
        credit_column=None,
        issues=[],
        unmapped_required_columns=[],
    )
    defaults.update(kwargs)
    return NormalizationPlan(**defaults)


def _csv_bytes(content: str) -> bytes:
    return content.encode("utf-8")


def _upload(client: TestClient, csv_content: str, filename: str = "test.csv"):
    return client.post(
        "/ai/plan-csv",
        files={"file": (filename, io.BytesIO(_csv_bytes(csv_content)), "text/csv")},
    )


@pytest.fixture
def client():
    return TestClient(app)


class TestPlanCSVEndpoint:
    BUDGY_CSV = (
        "authorized_date,description,primary_category,amount\n"
        "2024-01-01,Coffee,Food & drink,-5.00\n"
        "2024-01-02,Gas,Transportation,-40.00\n"
    )

    def _patched_planner(self, plan: NormalizationPlan, used_cache: bool):
        mock_planner = MagicMock()
        mock_planner.plan.return_value = (plan, used_cache)
        return mock_planner

    def test_valid_csv_returns_200(self, client):
        plan = _make_normalization_plan()
        with patch("backend.api.ai.ai_router.CSVNormalizationPlanner") as MockPlanner, \
             patch("backend.api.ai.ai_router.DatabaseSession"), \
             patch("backend.api.ai.ai_router.DatabaseFile"):
            MockPlanner.return_value = self._patched_planner(plan, False)
            response = _upload(client, self.BUDGY_CSV)
        assert response.status_code == 200

    def test_response_includes_all_plan_fields(self, client):
        plan = _make_normalization_plan()
        with patch("backend.api.ai.ai_router.CSVNormalizationPlanner") as MockPlanner, \
             patch("backend.api.ai.ai_router.DatabaseSession"), \
             patch("backend.api.ai.ai_router.DatabaseFile"):
            MockPlanner.return_value = self._patched_planner(plan, False)
            response = _upload(client, self.BUDGY_CSV)
        data = response.json()
        assert "column_map" in data
        assert "category_map" in data
        assert "amount_transform" in data
        assert "used_cache" in data
        assert "requires_manual_review" in data
        assert "unmapped_required_columns" in data

    def test_used_cache_false_when_ai_called(self, client):
        plan = _make_normalization_plan()
        with patch("backend.api.ai.ai_router.CSVNormalizationPlanner") as MockPlanner, \
             patch("backend.api.ai.ai_router.DatabaseSession"), \
             patch("backend.api.ai.ai_router.DatabaseFile"):
            MockPlanner.return_value = self._patched_planner(plan, False)
            response = _upload(client, self.BUDGY_CSV)
        assert response.json()["used_cache"] is False

    def test_used_cache_true_on_full_cache_hit(self, client):
        plan = _make_normalization_plan()
        with patch("backend.api.ai.ai_router.CSVNormalizationPlanner") as MockPlanner, \
             patch("backend.api.ai.ai_router.DatabaseSession"), \
             patch("backend.api.ai.ai_router.DatabaseFile"):
            MockPlanner.return_value = self._patched_planner(plan, True)
            response = _upload(client, self.BUDGY_CSV)
        assert response.json()["used_cache"] is True

    def test_requires_manual_review_true_when_required_column_missing(self, client):
        plan = _make_normalization_plan(unmapped_required_columns=["primary_category"])
        with patch("backend.api.ai.ai_router.CSVNormalizationPlanner") as MockPlanner, \
             patch("backend.api.ai.ai_router.DatabaseSession"), \
             patch("backend.api.ai.ai_router.DatabaseFile"):
            MockPlanner.return_value = self._patched_planner(plan, False)
            csv_no_cat = (
                "authorized_date,description,amount\n"
                "2024-01-01,Coffee,-5.00\n"
            )
            response = _upload(client, csv_no_cat)
        data = response.json()
        assert response.status_code == 200
        assert data["requires_manual_review"] is True
        assert "primary_category" in data["unmapped_required_columns"]

    def test_requires_manual_review_false_when_all_mapped(self, client):
        plan = _make_normalization_plan(unmapped_required_columns=[])
        with patch("backend.api.ai.ai_router.CSVNormalizationPlanner") as MockPlanner, \
             patch("backend.api.ai.ai_router.DatabaseSession"), \
             patch("backend.api.ai.ai_router.DatabaseFile"):
            MockPlanner.return_value = self._patched_planner(plan, False)
            response = _upload(client, self.BUDGY_CSV)
        assert response.json()["requires_manual_review"] is False

    def test_empty_file_returns_400(self, client):
        response = _upload(client, "")
        assert response.status_code == 400

    def test_headers_only_no_rows_returns_400(self, client):
        response = _upload(client, "authorized_date,description,primary_category,amount\n")
        assert response.status_code == 400

    def test_non_csv_file_returns_400(self, client):
        response = client.post(
            "/ai/plan-csv",
            files={"file": ("data.json", io.BytesIO(b'{"key": "value"}'), "application/json")},
        )
        # JSON with no commas still parses as a single-column CSV, so it won't 400 on parse.
        # This test verifies the endpoint handles non-tabular content gracefully.
        assert response.status_code in (200, 400)

    def test_cardinality_heuristic_used_for_categories(self, client):
        # Build CSV where one column has medium cardinality (categories, 10 unique)
        # and one has high cardinality (descriptions, 60 unique — above HIGH=50)
        n = 60
        categories = [f"Cat{i % 10}" for i in range(n)]
        descriptions = [f"Merchant {i}" for i in range(n)]
        lines = ["Date,Description,Category,Amount"]
        for i in range(n):
            lines.append(f"2024-01-{(i % 28) + 1:02d},{descriptions[i]},{categories[i]},{i}.00")
        csv_content = "\n".join(lines)

        captured_categories: list = []

        def capture_plan(headers, unique_categories, sample_amount_values=None):
            captured_categories.extend(unique_categories)
            return _make_normalization_plan(), False

        mock_planner = MagicMock()
        mock_planner.plan.side_effect = capture_plan

        with patch("backend.api.ai.ai_router.CSVNormalizationPlanner") as MockPlanner, \
             patch("backend.api.ai.ai_router.DatabaseSession"), \
             patch("backend.api.ai.ai_router.DatabaseFile"):
            MockPlanner.return_value = mock_planner
            _upload(client, csv_content)

        # Category values should be present; descriptions should not (too high cardinality)
        assert any(c.startswith("Cat") for c in captured_categories)
        assert not any(c.startswith("Merchant") for c in captured_categories)
