#!python3
"""
backend.api.categories.categories_router

Serves the category hierarchy (primary categories, detailed subcategories, and
exclude-from-analysis categories) derived from the authoritative Python enums in
analysis_utils.py. No database access — purely enum-derived data.
"""
from fastapi import APIRouter

from backend.utils.api_utils import RouterPrefixes
from backend.utils.analysis_utils import CATEGORY_MAPPING, EXCLUDE_CATEGORIES, PrimaryCategories

router = APIRouter(prefix=RouterPrefixes.CATEGORIES.value, tags=["Categories"])


@router.get("")
def get_categories() -> dict:
    """
    Returns the full category hierarchy used by the frontend for dropdowns and filters.

    Response shape:
      primaryCategories  — ordered list of all 16 primary category display names
      categoryMapping    — maps each primary name to its list of detailed subcategory names
      excludeCategories  — detailed categories excluded from spending analysis
    """
    return {
        "primaryCategories": [c.value for c in PrimaryCategories],
        "categoryMapping": {
            k.value: [v.value for v in vs] for k, vs in CATEGORY_MAPPING.items()
        },
        "excludeCategories": [c.value for c in EXCLUDE_CATEGORIES],
    }
