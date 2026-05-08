#!python3
from datetime import datetime
from typing import Optional

from backend.ai_modules.csv_normalization_service.normalization_plan import NormalizationPlan


def _try_parse_date(val: str) -> Optional[str]:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%Y/%m/%d",
                "%d-%b-%Y", "%b %d %Y", "%B %d %Y", "%d %b %Y"):
        try:
            return datetime.strptime(val.strip(), fmt).strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            continue
    return val.strip() if val else val


def _fields_match(got, expected) -> bool:
    if expected is None and got is None:
        return True
    if expected is None or got is None:
        return False
    if isinstance(expected, (int, float)):
        try:
            return abs(float(got) - float(expected)) <= 0.01
        except (TypeError, ValueError):
            return False
    if isinstance(expected, str) and isinstance(got, str):
        norm_got = _try_parse_date(got)
        norm_exp = _try_parse_date(expected)
        return norm_got.lower() == norm_exp.lower()
    return str(got).strip() == str(expected).strip()


def score_plan(ai_plan: NormalizationPlan, sidecar: dict) -> dict:
    """
    Score the AI-produced NormalizationPlan against the ideal plan in the sidecar.

    Returns a dict with column_map, category_map, and amount_transform sub-scores.
    """
    ideal = sidecar.get("ideal_plan", {})

    # ── Column map ────────────────────────────────────────────────────────────
    ideal_col = ideal.get("column_map", {})
    total_cols = len(ideal_col)
    correct_cols = 0
    col_misses: dict = {}

    for raw_header, expected_field in ideal_col.items():
        got = ai_plan.column_map.get(raw_header)
        if got == expected_field:
            correct_cols += 1
        else:
            col_misses[raw_header] = {"expected": expected_field, "got": got}

    col_score = correct_cols / total_cols if total_cols > 0 else 1.0

    # ── Category map ──────────────────────────────────────────────────────────
    ideal_cat = ideal.get("category_map", {})
    total_cats = len(ideal_cat)
    correct_cats = 0
    cat_misses: dict = {}

    for raw_cat, expected_mapping in ideal_cat.items():
        got_mapping = ai_plan.category_map.get(raw_cat)
        if (got_mapping
                and got_mapping.primary == expected_mapping.get("primary")
                and got_mapping.detailed == expected_mapping.get("detailed")):
            correct_cats += 1
        else:
            cat_misses[raw_cat] = {
                "expected": expected_mapping,
                "got": {"primary": got_mapping.primary, "detailed": got_mapping.detailed}
                       if got_mapping else None,
            }

    cat_score = correct_cats / total_cats if total_cats > 0 else 1.0

    # ── Amount transform ──────────────────────────────────────────────────────
    expected_transform = ideal.get("amount_transform")
    got_transform = ai_plan.amount_transform.value
    transform_correct = got_transform == expected_transform
    transform_score = 1.0 if transform_correct else 0.0

    debit_col_ok = True
    credit_col_ok = True
    if expected_transform == "debit_credit":
        debit_col_ok = ai_plan.debit_column == ideal.get("debit_column")
        credit_col_ok = ai_plan.credit_column == ideal.get("credit_column")

    return {
        "column_map": {
            "score": round(col_score, 4),
            "correct": correct_cols,
            "total": total_cols,
            "misses": col_misses,
        },
        "category_map": {
            "score": round(cat_score, 4),
            "correct": correct_cats,
            "total": total_cats,
            "misses": cat_misses,
        },
        "amount_transform": {
            "score": round(transform_score, 4),
            "expected": expected_transform,
            "got": got_transform,
            "debit_column_ok": debit_col_ok,
            "credit_column_ok": credit_col_ok,
        },
    }


def score_rows(transformed_rows: list[dict], expected_rows: list[dict]) -> dict:
    """
    Score transformed rows against expected rows from the sidecar.

    Matches rows by (authorized_date, description) key pair.
    Compares each field with type-appropriate tolerance (±0.01 for floats,
    date normalization for date strings, case-insensitive for other strings).
    """
    if not expected_rows:
        return {"score": 1.0, "matched": 0, "total": 0, "mismatches": []}

    # Build lookup keyed by (normalized_date, lower_description)
    lookup: dict = {}
    for row in transformed_rows:
        date_raw = row.get("authorized_date", "") or ""
        desc_raw = row.get("description", "") or ""
        key = (_try_parse_date(str(date_raw)), str(desc_raw).lower().strip())
        lookup[key] = row

    matched = 0
    total = len(expected_rows)
    mismatches: list[dict] = []

    for expected in expected_rows:
        date_raw = expected.get("authorized_date", "") or ""
        desc_raw = expected.get("description", "") or ""
        key = (_try_parse_date(str(date_raw)), str(desc_raw).lower().strip())
        got_row = lookup.get(key)

        if got_row is None:
            mismatches.append({
                "key": {"authorized_date": date_raw, "description": desc_raw},
                "reason": "row not found in transformed output",
            })
            continue

        field_mismatches: dict = {}
        for field, expected_val in expected.items():
            got_val = got_row.get(field)
            if not _fields_match(got_val, expected_val):
                field_mismatches[field] = {"expected": expected_val, "got": got_val}

        if not field_mismatches:
            matched += 1
        else:
            mismatches.append({
                "key": {"authorized_date": date_raw, "description": desc_raw},
                "reason": "field mismatches",
                "fields": field_mismatches,
            })

    return {
        "score": round(matched / total, 4) if total > 0 else 1.0,
        "matched": matched,
        "total": total,
        "mismatches": mismatches,
    }
