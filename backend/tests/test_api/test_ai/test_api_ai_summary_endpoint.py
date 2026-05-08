#!python3
"""
Tests for POST /ai/summary endpoint.

AISummaryService is patched so no real DB or AI calls are made.
Tests cover: happy path, 404 on missing data, 422 on bad format,
503/504 on AI errors.
"""
import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.ai_modules.ai_errors import AIAuthError, AITimeoutError
from backend.api.ai.ai_models import AISummaryData
from backend.main import app

client = TestClient(app)

_GOOD_SUMMARY = AISummaryData(
    generated_at=datetime(2025, 1, 31, 12, 0, 0, tzinfo=timezone.utc),
    recap="You spent $1,200 and earned $3,000.",
    anomalies=["Food & drink is 116% of budget."],
    suggestions=["Cook at home more."],
)


def _patch_summary_service(return_value=None, side_effect=None):
    """Patch AISummaryService.summarize and build_period_summary together."""
    return return_value, side_effect


# ─── Happy path ───────────────────────────────────────────────────────────────

class TestAISummaryEndpointHappyPath:
    def test_monthly_returns_200(self):
        mock_summary_resp = MagicMock()
        with (
            patch("backend.api.ai.ai_router.build_period_summary", return_value=mock_summary_resp),
            patch("backend.api.ai.ai_router.AISummaryService") as MockService,
            patch("backend.api.ai.ai_router._make_ai_client", return_value=MagicMock()),
        ):
            MockService.return_value.summarize.return_value = _GOOD_SUMMARY
            response = client.post("/ai/summary", json={"month": "2025-01"})

        assert response.status_code == 200

    def test_response_has_data_envelope(self):
        mock_summary_resp = MagicMock()
        with (
            patch("backend.api.ai.ai_router.build_period_summary", return_value=mock_summary_resp),
            patch("backend.api.ai.ai_router.AISummaryService") as MockService,
            patch("backend.api.ai.ai_router._make_ai_client", return_value=MagicMock()),
        ):
            MockService.return_value.summarize.return_value = _GOOD_SUMMARY
            response = client.post("/ai/summary", json={"month": "2025-01"})

        body = response.json()
        assert "data" in body

    def test_response_data_has_required_fields(self):
        mock_summary_resp = MagicMock()
        with (
            patch("backend.api.ai.ai_router.build_period_summary", return_value=mock_summary_resp),
            patch("backend.api.ai.ai_router.AISummaryService") as MockService,
            patch("backend.api.ai.ai_router._make_ai_client", return_value=MagicMock()),
        ):
            MockService.return_value.summarize.return_value = _GOOD_SUMMARY
            response = client.post("/ai/summary", json={"month": "2025-01"})

        data = response.json()["data"]
        assert "generatedAt" in data
        assert "recap" in data
        assert "anomalies" in data
        assert "suggestions" in data

    def test_yearly_period_accepted(self):
        mock_summary_resp = MagicMock()
        with (
            patch("backend.api.ai.ai_router.build_period_summary", return_value=mock_summary_resp),
            patch("backend.api.ai.ai_router.AISummaryService") as MockService,
            patch("backend.api.ai.ai_router._make_ai_client", return_value=MagicMock()),
        ):
            MockService.return_value.summarize.return_value = _GOOD_SUMMARY
            response = client.post("/ai/summary", json={"month": "2025"})

        assert response.status_code == 200


# ─── Error cases ──────────────────────────────────────────────────────────────

class TestAISummaryEndpointErrors:
    def test_404_when_no_summary_data(self):
        with patch("backend.api.ai.ai_router.build_period_summary", return_value=None):
            response = client.post("/ai/summary", json={"month": "2025-01"})
        assert response.status_code == 404

    def test_503_on_ai_auth_error(self):
        mock_summary_resp = MagicMock()
        with (
            patch("backend.api.ai.ai_router.build_period_summary", return_value=mock_summary_resp),
            patch("backend.api.ai.ai_router.AISummaryService") as MockService,
            patch("backend.api.ai.ai_router._make_ai_client", return_value=MagicMock()),
        ):
            MockService.return_value.summarize.side_effect = AIAuthError("invalid key")
            response = client.post("/ai/summary", json={"month": "2025-01"})

        assert response.status_code == 503

    def test_504_on_ai_timeout_error(self):
        mock_summary_resp = MagicMock()
        with (
            patch("backend.api.ai.ai_router.build_period_summary", return_value=mock_summary_resp),
            patch("backend.api.ai.ai_router.AISummaryService") as MockService,
            patch("backend.api.ai.ai_router._make_ai_client", return_value=MagicMock()),
        ):
            MockService.return_value.summarize.side_effect = AITimeoutError("timed out")
            response = client.post("/ai/summary", json={"month": "2025-01"})

        assert response.status_code == 504

    def test_missing_month_field_returns_422(self):
        response = client.post("/ai/summary", json={})
        assert response.status_code == 422
