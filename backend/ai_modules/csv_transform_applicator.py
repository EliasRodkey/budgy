#!python3
from typing import Optional

from backend.ai_modules.normalization_plan import AmountTransform, CategoryMapping, NormalizationPlan
from backend.ai_modules.ai_client_service import ALL_SCHEMA_FIELDS, REQUIRED_SCHEMA_FIELDS

from pleasant_loggers import get_logger
logger = get_logger(__name__)


class TransformValidationError(Exception):
    """Raised when rows are missing required schema fields after transformation."""

    def __init__(self, failed_rows: list[dict]):
        self.failed_rows = failed_rows
        super().__init__(
            f"{len(failed_rows)} row(s) missing required fields after transformation"
        )


import re as _re
_CURRENCY_STRIP = _re.compile(r"[^\d.\-+]")


def _parse_amount(value: str) -> float:
    """Parse an amount string, stripping currency symbols, spaces, and commas."""
    return float(_CURRENCY_STRIP.sub("", str(value).strip()))


def apply_normalization_plan(
    rows: list[dict[str, str]],
    plan: NormalizationPlan,
) -> list[dict]:
    """
    Apply a NormalizationPlan to raw CSV rows.

    Returns transformed rows whose keys are Budgy schema field names.
    Raises TransformValidationError if any rows are missing required fields
    after transformation.
    """
    _schema_field_set = set(ALL_SCHEMA_FIELDS)
    transformed = []

    for raw_row in rows:
        new_row: dict = {}

        # 1. Column renames
        for raw_col, raw_val in raw_row.items():
            mapped = plan.column_map.get(raw_col)
            if mapped is not None:
                new_row[mapped] = raw_val
            elif raw_col in _schema_field_set and raw_col not in plan.column_map:
                new_row[raw_col] = raw_val
            # else: unknown/unmapped column — drop it

        # 2. Category substitution
        # After column rename, primary_category holds the raw category value string.
        # Look it up in category_map and expand to primary + detailed.
        raw_cat_val: Optional[str] = new_row.get("primary_category")
        if raw_cat_val is not None:
            mapping: Optional[CategoryMapping] = plan.category_map.get(raw_cat_val)
            if mapping:
                new_row["primary_category"] = mapping.primary
                new_row["detailed_category"] = mapping.detailed

        # 3. Amount normalization
        if plan.amount_transform == AmountTransform.SIGNED:
            if "amount" in new_row:
                new_row["amount"] = _parse_amount(new_row["amount"])

        elif plan.amount_transform == AmountTransform.INVERT:
            if "amount" in new_row:
                new_row["amount"] = -_parse_amount(new_row["amount"])

        elif plan.amount_transform == AmountTransform.DEBIT_CREDIT:
            debit = _parse_amount(raw_row.get(plan.debit_column) or "0")
            credit = _parse_amount(raw_row.get(plan.credit_column) or "0")
            new_row["amount"] = credit - debit

        transformed.append(new_row)

    # 4. Validate required fields
    failed_rows = []
    for i, row in enumerate(transformed):
        missing = [f for f in REQUIRED_SCHEMA_FIELDS if f not in row or row[f] == ""]
        if missing:
            failed_rows.append({"row_index": i, "missing_fields": missing})

    if failed_rows:
        raise TransformValidationError(failed_rows)

    logger.info(f"Transformation complete: {len(transformed)} rows transformed")
    return transformed
