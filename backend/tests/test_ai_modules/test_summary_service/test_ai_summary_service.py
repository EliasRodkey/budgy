#!python3
"""
Tests for AISummaryService.

The AIClient is mocked so no real API calls are made.
Tests verify prompt construction (via _build_user_message) and that
the tool response is correctly parsed into an AISummaryData.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from backend.ai_modules.summary_service.ai_summary_service import AISummaryService, _build_user_message
from backend.api.ai.ai_models import AISummaryData
from backend.utils.summary_utils import CategorySpendResponse, MonthlySummaryResponse


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def _make_summary(month: str = "2025-01", with_budget: bool = False) -> MonthlySummaryResponse:
    food = CategorySpendResponse(
        category_id="Food & drink",
        category_name="Food & drink",
        amount=350.0,
        transaction_count=8,
        avg_per_transaction=43.75,
        monthly_limit=300.0 if with_budget else None,
        percent_of_limit=116.7 if with_budget else None,
        is_over_budget=with_budget,
    )
    income = CategorySpendResponse(
        category_id="Income",
        category_name="Income",
        amount=0.0,
        transaction_count=0,
        avg_per_transaction=0.0,
        monthly_limit=None,
        percent_of_limit=None,
        is_over_budget=False,
    )
    return MonthlySummaryResponse(
        month=month,
        total_income=3000.0,
        total_expenses=1200.0,
        net=1800.0,
        by_category=[food, income],
    )


def _make_tool_response(recap="Good month.", anomalies=None, suggestions=None) -> dict:
    return {
        "recap": recap,
        "anomalies": anomalies or [],
        "suggestions": suggestions or ["Reduce dining out."],
    }


# ─── _build_user_message ──────────────────────────────────────────────────────

class TestBuildUserMessage:
    def test_contains_period(self):
        msg = _build_user_message(_make_summary("2025-03"))
        assert "2025-03" in msg

    def test_contains_income(self):
        msg = _build_user_message(_make_summary())
        assert "$3,000.00" in msg

    def test_contains_expenses(self):
        msg = _build_user_message(_make_summary())
        assert "$1,200.00" in msg

    def test_contains_net(self):
        msg = _build_user_message(_make_summary())
        assert "$1,800.00" in msg

    def test_contains_non_zero_category(self):
        msg = _build_user_message(_make_summary())
        assert "Food & drink" in msg
        assert "$350.00" in msg

    def test_zero_amount_categories_omitted(self):
        msg = _build_user_message(_make_summary())
        assert "Income: $0" not in msg

    def test_budget_info_included_when_present(self):
        msg = _build_user_message(_make_summary(with_budget=True))
        assert "budget" in msg.lower()
        assert "over budget" in msg.lower()

    def test_no_budget_info_when_absent(self):
        msg = _build_user_message(_make_summary(with_budget=False))
        assert "budget" not in msg.lower()


# ─── AISummaryService.summarize ───────────────────────────────────────────────

class TestAISummaryService:
    def _make_service(self, tool_response: dict) -> AISummaryService:
        client = MagicMock()
        client.complete_with_tool.return_value = tool_response
        return AISummaryService(client)

    def test_returns_ai_summary_data(self):
        service = self._make_service(_make_tool_response())
        result = service.summarize(_make_summary())
        assert isinstance(result, AISummaryData)

    def test_recap_populated(self):
        service = self._make_service(_make_tool_response(recap="Great month overall."))
        result = service.summarize(_make_summary())
        assert result.recap == "Great month overall."

    def test_anomalies_populated(self):
        anomalies = ["Food & drink is 116% of budget."]
        service = self._make_service(_make_tool_response(anomalies=anomalies))
        result = service.summarize(_make_summary())
        assert result.anomalies == anomalies

    def test_suggestions_populated(self):
        suggestions = ["Cook at home more.", "Cancel unused subscriptions."]
        service = self._make_service(_make_tool_response(suggestions=suggestions))
        result = service.summarize(_make_summary())
        assert result.suggestions == suggestions

    def test_empty_anomalies_allowed(self):
        service = self._make_service(_make_tool_response(anomalies=[]))
        result = service.summarize(_make_summary())
        assert result.anomalies == []

    def test_generated_at_is_recent(self):
        service = self._make_service(_make_tool_response())
        before = datetime.now(tz=timezone.utc)
        result = service.summarize(_make_summary())
        after = datetime.now(tz=timezone.utc)
        assert before <= result.generated_at <= after

    def test_client_called_once(self):
        client = MagicMock()
        client.complete_with_tool.return_value = _make_tool_response()
        service = AISummaryService(client)
        service.summarize(_make_summary())
        client.complete_with_tool.assert_called_once()

    def test_ai_errors_propagate(self):
        from backend.ai_modules.ai_errors import AIAuthError
        client = MagicMock()
        client.complete_with_tool.side_effect = AIAuthError("bad key")
        service = AISummaryService(client)
        with pytest.raises(AIAuthError):
            service.summarize(_make_summary())
