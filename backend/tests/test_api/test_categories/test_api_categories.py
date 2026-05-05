#!python3
"""
Tests for the GET /api/categories endpoint.

The endpoint is pure enum-derived data (no DB), so these tests call the handler
function directly and cross-validate the response against the Python source-of-truth.
"""
import pytest

from backend.api.categories.categories_router import get_categories
from backend.utils.analysis_utils import (
    CATEGORY_MAPPING,
    EXCLUDE_CATEGORIES,
    DetailedCategories,
    PrimaryCategories,
)


@pytest.fixture
def response():
    return get_categories()


class TestGetCategories:
    def test_returns_200_shape(self, response):
        assert "primaryCategories" in response
        assert "categoryMapping" in response
        assert "excludeCategories" in response

    def test_primary_categories_count(self, response):
        assert len(response["primaryCategories"]) == 16

    def test_primary_categories_match_enum(self, response):
        expected = [c.value for c in PrimaryCategories]
        assert response["primaryCategories"] == expected

    def test_category_mapping_keys_are_primary_categories(self, response):
        primary_set = set(response["primaryCategories"])
        for key in response["categoryMapping"]:
            assert key in primary_set

    def test_category_mapping_values_are_nonempty_except_other(self, response):
        for primary, detailed in response["categoryMapping"].items():
            if primary == "Other":
                continue
            assert len(detailed) > 0, f"{primary} has no detailed categories"

    def test_category_mapping_matches_source_of_truth(self, response):
        expected = {k.value: [v.value for v in vs] for k, vs in CATEGORY_MAPPING.items()}
        assert response["categoryMapping"] == expected

    def test_exclude_categories_match_source_of_truth(self, response):
        expected = [c.value for c in EXCLUDE_CATEGORIES]
        assert response["excludeCategories"] == expected

    def test_exclude_categories_are_valid_detailed_categories(self, response):
        all_detailed = {c.value for c in DetailedCategories}
        for cat in response["excludeCategories"]:
            assert cat in all_detailed, f"{cat!r} is not a valid DetailedCategories value"
