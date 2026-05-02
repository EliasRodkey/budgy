#!python3
"""
backend.api.ai.ai_router
FastAPI router for AI-assisted CSV normalization endpoints.
"""
import csv
import io
import re
from pleasant_loggers import get_logger

import anthropic
from fastapi import APIRouter, File, HTTPException, UploadFile

from pleasant_database import DatabaseFile

from backend.ai_modules.ai_client_service import AIClientService
from backend.ai_modules.csv_normalization_planner import CSVNormalizationPlanner
from backend.api.ai.ai_models import PlanCSVResponse
from backend.csv_modules.csv_parser import unwrap_row_quotes
from backend.database_modules.db_session import DatabaseSession
from backend.utils.api_utils import RouterPrefixes
from backend.utils.file_utils import EDirectories

logger = get_logger(__name__)

router = APIRouter(prefix=RouterPrefixes.AI.value, tags=["AI"])

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$|^\d{1,2}/\d{1,2}/\d{2,4}$")
_CATEGORY_LOW = 6
_CATEGORY_HIGH = 50


def _is_numeric_or_date(val: str) -> bool:
    try:
        float(val.replace(",", ""))
        return True
    except ValueError:
        pass
    return bool(_DATE_PATTERN.match(val))


def _extract_sample_amounts(rows: list[dict], headers: list[str], sample_size: int = 10) -> dict[str, list[float]]:
    """
    Returns up to sample_size parsed float values for each column that looks numeric
    (≥50% of sampled values are parseable as floats). Used to give the AI concrete
    data for sign convention detection rather than relying on header names alone.
    """
    result: dict[str, list[float]] = {}
    sample_rows = rows[:max(sample_size * 2, 20)]
    _strip = re.compile(r"[^\d.\-+]")
    for header in headers:
        raw_vals: list[str] = []
        floats: list[float] = []
        for r in sample_rows:
            if not r.get(header):
                continue
            original = str(r[header]).strip()
            if _DATE_PATTERN.match(original):
                continue  # exclude date-like values so date columns don't appear as numeric
            stripped = _strip.sub("", original)
            raw_vals.append(stripped)
            try:
                floats.append(float(stripped))
            except ValueError:
                pass
        if len(raw_vals) > 0 and len(floats) / len(raw_vals) >= 0.5:
            result[header] = floats[:sample_size]
    return result


def _extract_candidate_categories(rows: list[dict], headers: list[str]) -> list[str]:
    """
    Returns unique string values from columns whose cardinality falls in the
    6–50 range — a heuristic for identifying category columns over amounts,
    dates, and descriptions. Falls back to all non-numeric/date string values
    if no candidate columns are found.
    """
    candidates: set[str] = set()
    for header in headers:
        vals = [str(r[header]) for r in rows if r.get(header)]
        non_numeric = [v for v in vals if v and not _is_numeric_or_date(v)]
        unique = set(non_numeric)
        if _CATEGORY_LOW <= len(unique) <= _CATEGORY_HIGH:
            candidates.update(unique)

    if not candidates:
        for header in headers:
            vals = [str(r[header]) for r in rows if r.get(header)]
            candidates.update(v for v in vals if v and not _is_numeric_or_date(v))

    return list(candidates)


@router.post("/plan-csv", response_model=PlanCSVResponse)
async def plan_csv(file: UploadFile = File(...)) -> PlanCSVResponse:
    """
    Accepts a multipart CSV file, runs CSVNormalizationPlanner, and returns a
    NormalizationPlan JSON for the frontend review step. Does not import data.

    Returns requires_manual_review: true when any required column (date, description,
    primary_category, amount) could not be mapped — the frontend should show
    column-selector dropdowns for each unmapped field.
    """
    contents = await file.read()
    try:
        text = contents.decode("utf-8")
    except UnicodeDecodeError:
        text = contents.decode("latin-1")

    try:
        text = unwrap_row_quotes(text)
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        headers = list(reader.fieldnames or [])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {exc}") from exc

    if not headers:
        raise HTTPException(status_code=400, detail="CSV has no headers.")
    if not rows:
        raise HTTPException(status_code=400, detail="CSV is empty.")

    unique_categories = _extract_candidate_categories(rows, headers)
    sample_amounts = _extract_sample_amounts(rows, headers)
    logger.info(
        "plan-csv: %d headers, %d candidate category values, %d numeric columns sampled",
        len(headers),
        len(unique_categories),
        len(sample_amounts),
    )

    db_file = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)
    session = DatabaseSession(db_file)
    try:
        planner = CSVNormalizationPlanner(session.category_mapping_rules, AIClientService())
        plan, used_cache = planner.plan(headers, unique_categories, sample_amount_values=sample_amounts)
    except anthropic.AuthenticationError as exc:
        logger.error(f"Anthropic API key missing or invalid: {exc}")
        raise HTTPException(
            status_code=503,
            detail="AI service is not configured. Ensure ANTHROPIC_API_KEY is set in your .env file.",
        ) from exc
    except anthropic.BadRequestError as exc:
        if "credit balance is too low" in str(exc).lower():
            logger.error(f"Anthropic account out of credits: {exc}")
            raise HTTPException(
                status_code=402,
                detail="Anthropic account has no credits. Add credits at console.anthropic.com/settings/billing.",
            ) from exc
        logger.error(f"Anthropic bad request during CSV analysis: {exc}")
        raise HTTPException(status_code=400, detail=f"AI service rejected the request: {exc}") from exc
    except anthropic.APIError as exc:
        logger.error(f"Anthropic API error during CSV analysis: {exc}")
        raise HTTPException(
            status_code=502,
            detail=f"AI service error: {exc}",
        ) from exc
    except Exception as exc:
        logger.error(f"Unexpected error during CSV analysis: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"CSV analysis failed: {exc}",
        ) from exc
    finally:
        session.close()

    return PlanCSVResponse(
        **plan.model_dump(),
        used_cache=used_cache,
        requires_manual_review=bool(plan.unmapped_required_columns),
    )
