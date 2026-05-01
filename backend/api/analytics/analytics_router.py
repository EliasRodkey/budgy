#!python3
"""
backend.api.analytics.analytics_router
GET /analytics/series — returns full AnalyticsData (series, incomeExpenses, budgetPerformance, monthlyBudgetTotals).
"""
from pleasant_loggers import get_logger
from fastapi import APIRouter, Depends, HTTPException

from pleasant_database import DatabaseFile

from backend.database_modules.db_session import DatabaseSession
from backend.utils.analysis_utils import PrimaryCategories
from backend.utils.api_utils import RouterPrefixes
from backend.utils.file_utils import EDirectories

logger = get_logger(__name__)

router = APIRouter(prefix=RouterPrefixes.ANALYTICS.value, tags=["Analytics"])

# Build a stable mapping once at import time
# snake_case key → display name  (e.g. "food_and_drink" → "Food & drink")
_SNAKE_TO_DISPLAY: dict[str, str] = dict(
    zip(PrimaryCategories.as_snake_case_headers(), PrimaryCategories.as_list())
)
# All expense category snake_case keys (income excluded)
_EXPENSE_KEYS: list[str] = [k for k in _SNAKE_TO_DISPLAY if k != "income"]


def get_db():
    db_file = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)
    session = DatabaseSession(db_file)
    try:
        yield session
    finally:
        session.close()


def _month_str(year: int, month: int) -> str:
    return f"{year}-{month:02d}"


def _parse_yyyymm(value: str, param_name: str) -> tuple[int, int]:
    try:
        year, month = value.split("-")
        return int(year), int(month)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=422, detail=f"{param_name} must be in YYYY-MM format")


@router.get("/series")
async def get_analytics_series(
    date_from: str,
    date_to: str,
    db: DatabaseSession = Depends(get_db),
) -> dict:
    """
    Returns AnalyticsData for the requested month range.
    date_from / date_to are YYYY-MM strings (inclusive).
    """
    from_year, from_month = _parse_yyyymm(date_from, "date_from")
    to_year, to_month = _parse_yyyymm(date_to, "date_to")

    from_ord = from_year * 12 + from_month
    to_ord = to_year * 12 + to_month

    if from_ord > to_ord:
        raise HTTPException(status_code=422, detail="date_from must be <= date_to")

    # ── 1. Fetch summaries in range ───────────────────────────────────────────
    all_summaries = db.summaries.fetch_all_items()
    rows = sorted(
        [r for r in all_summaries if from_ord <= r.year * 12 + r.month <= to_ord],
        key=lambda r: (r.year, r.month),
    )

    labels: list[str] = [_month_str(r.year, r.month) for r in rows]

    # ── 2. AnalyticsSeries ────────────────────────────────────────────────────
    datasets = []
    for snake_key, display_name in _SNAKE_TO_DISPLAY.items():
        if snake_key == "income":
            continue
        col = f"sum_{snake_key}"
        values = [abs(getattr(r, col, 0) or 0) for r in rows]
        if any(v > 0 for v in values):
            datasets.append({
                "categoryId": snake_key,
                "categoryName": display_name,
                "values": values,
            })

    series = {"labels": labels, "datasets": datasets}

    # ── 3. incomeExpenses ─────────────────────────────────────────────────────
    income_expenses = []
    for r in rows:
        income = abs(getattr(r, "sum_income", 0) or 0)
        expenses = sum(abs(getattr(r, f"sum_{k}", 0) or 0) for k in _EXPENSE_KEYS)
        income_expenses.append({
            "month": _month_str(r.year, r.month),
            "income": income,
            "expenses": expenses,
            "net": income - expenses,
        })

    # ── 4. budgetPerformance ──────────────────────────────────────────────────
    all_assignments = db.budget_assignments.get_all()
    # Pre-load all budgets referenced by assignments into a dict
    referenced_budget_ids = {a.budget_id for a in all_assignments}
    budgets_by_id: dict[int, object] = {}
    for bid in referenced_budget_ids:
        try:
            budgets_by_id[bid] = db.budgets.fetch_item_by_id(bid)
        except Exception:
            pass

    # categoryId → per-month data accumulator
    category_data: dict[str, dict] = {}

    for label, row in zip(labels, rows):
        assignment = db.budget_assignments.get_effective_assignment(label)
        budget = budgets_by_id.get(assignment.budget_id) if assignment else None

        # Income card
        income_actual = abs(getattr(row, "sum_income", 0) or 0)
        income_limit = getattr(budget, "income", 0) if budget else 0
        _accumulate(category_data, "income", "Income", True, income_limit, label, income_actual - income_limit)

        # Expense categories
        for snake_key, display_name in _SNAKE_TO_DISPLAY.items():
            if snake_key == "income":
                continue
            actual = abs(getattr(row, f"sum_{snake_key}", 0) or 0)
            limit = getattr(budget, snake_key, 0) if budget else 0
            limit = limit or 0
            over_under = actual - limit
            _accumulate(category_data, snake_key, display_name, False, limit, label, over_under)

    budget_performance = []
    for cat_id, entry in category_data.items():
        data_points = [{"month": m, "overUnder": entry["points"][m]} for m in labels]
        avg = sum(d["overUnder"] for d in data_points) / max(len(data_points), 1)
        budget_performance.append({
            "categoryId": cat_id,
            "categoryName": entry["categoryName"],
            "monthlyLimit": entry["monthlyLimit"],
            "isIncome": entry["isIncome"],
            "data": data_points,
            "averageOverUnder": avg,
        })

    # Sort: worst expense performers first (highest avg overUnder), income last
    budget_performance.sort(key=lambda x: (x["isIncome"], -x["averageOverUnder"]))

    # ── 5. monthlyBudgetTotals ────────────────────────────────────────────────
    expense_perf = [c for c in budget_performance if not c["isIncome"]]
    monthly_budget_totals = [
        {
            "month": label,
            "overUnder": sum(
                next((d["overUnder"] for d in c["data"] if d["month"] == label), 0)
                for c in expense_perf
            ),
        }
        for label in labels
    ]

    return {
        "data": {
            "series": series,
            "incomeExpenses": income_expenses,
            "budgetPerformance": budget_performance,
            "monthlyBudgetTotals": monthly_budget_totals,
        }
    }


def _accumulate(
    category_data: dict,
    cat_id: str,
    cat_name: str,
    is_income: bool,
    monthly_limit: float,
    month: str,
    over_under: float,
) -> None:
    if cat_id not in category_data:
        category_data[cat_id] = {
            "categoryName": cat_name,
            "isIncome": is_income,
            "monthlyLimit": monthly_limit,
            "points": {},
        }
    else:
        # Update limit to latest non-zero value seen (last active budget wins)
        if monthly_limit:
            category_data[cat_id]["monthlyLimit"] = monthly_limit
    category_data[cat_id]["points"][month] = over_under
