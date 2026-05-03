#!python3
from typing import Optional

from backend.ai_modules.normalization_plan import AmountTransform, CategoryMapping, NormalizationPlan
from backend.ai_modules.ai_client_service import ALL_SCHEMA_FIELDS, REQUIRED_SCHEMA_FIELDS
from backend.database_modules.models.common import TableStatus

from pleasant_loggers import get_logger
logger = get_logger(__name__)


import re as _re
_CURRENCY_STRIP = _re.compile(r"[^\d.\-+]")


def _parse_amount(value: str) -> Optional[float]:
    """Parse an amount string, stripping currency symbols. Returns None if unparseable."""
    try:
        cleaned = _CURRENCY_STRIP.sub("", str(value).strip())
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def _is_structurally_corrupt(raw_row: dict[str, str], expected_col_count: int) -> bool:
    """Return True if the row has the wrong number of columns or all values are empty."""
    if len(raw_row) != expected_col_count:
        return True
    return all(v.strip() == "" for v in raw_row.values())


def apply_normalization_plan(
    rows: list[dict[str, str]],
    plan: NormalizationPlan,
) -> tuple[list[dict], list[dict]]:
    """
    Apply a NormalizationPlan to raw CSV rows.

    Returns (transformed_rows, skipped_rows).
    - transformed_rows: rows with Budgy schema field names; rows with missing required
      fields are imported as UNCHECKED with "Other" as the fallback primary_category.
    - skipped_rows: list of {"row": int, "reason": str} for structurally corrupt rows.
    """
    _schema_field_set = set(ALL_SCHEMA_FIELDS)
    expected_col_count = len(rows[0]) if rows else 0
    transformed = []
    skipped: list[dict] = []

    for row_num, raw_row in enumerate(rows, start=1):
        # Skip structurally corrupt rows (wrong column count or entirely empty)
        if _is_structurally_corrupt(raw_row, expected_col_count):
            reason = (
                "wrong column count"
                if len(raw_row) != expected_col_count
                else "empty row"
            )
            skipped.append({"row": row_num, "reason": reason})
            continue

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
                parsed = _parse_amount(new_row["amount"])
                new_row["amount"] = -parsed if parsed is not None else None

        elif plan.amount_transform == AmountTransform.DEBIT_CREDIT:
            debit = _parse_amount(raw_row.get(plan.debit_column) or "0") or 0.0
            credit = _parse_amount(raw_row.get(plan.credit_column) or "0") or 0.0
            new_row["amount"] = credit - debit

        # 4. Soft-fail missing required fields — mark as UNCHECKED with "Other" fallback
        missing = [f for f in REQUIRED_SCHEMA_FIELDS if not new_row.get(f)]
        if missing:
            new_row["status"] = TableStatus.UNCHECKED.value
            if "primary_category" in missing:
                new_row["primary_category"] = "Other"
            # Leave other missing fields as None — user fixes via edit modal

        transformed.append(new_row)

    logger.info(
        f"Transformation complete: {len(transformed)} rows transformed, {len(skipped)} skipped"
    )
    return transformed, skipped
