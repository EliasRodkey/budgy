#!python3
import csv as csv_lib
import json
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"
RUNS_DIR = RESULTS_DIR / "runs"
CSV_FILE = RESULTS_DIR / "results.csv"
CSV_COLUMNS = [
    "timestamp", "model", "description", "fixture_name",
    "column_map_score", "category_map_score", "amount_transform_score",
    "row_score", "overall_score",
]


def write_results(fixture_name: str, result: dict, run_context: dict) -> None:
    timestamp = run_context["timestamp"]

    # 1. Timestamped JSON — full stage-by-stage detail, accumulated across all fixtures in the run
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_file = RUNS_DIR / f"{timestamp}.json"
    existing: dict = {}
    if run_file.exists():
        try:
            with open(run_file) as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            existing = {}
    existing.setdefault("fixtures", {})[fixture_name] = result
    existing["timestamp"] = timestamp
    existing["model"] = run_context["model"]
    existing["description"] = run_context["description"]
    with open(run_file, "w") as f:
        json.dump(existing, f, indent=2, default=str)

    # 2. Growing CSV — headline scores only, skipped if overall_score not yet computed
    if result.get("overall_score") is None:
        return
    plan_score = result["stages"].get("ai_planning", {}).get("plan_score", {})
    row_score = result["stages"].get("transform_application", {}).get("row_score", {})
    csv_row = {
        "timestamp": timestamp,
        "model": run_context["model"],
        "description": run_context["description"],
        "fixture_name": fixture_name,
        "column_map_score": plan_score.get("column_map", {}).get("score", ""),
        "category_map_score": plan_score.get("category_map", {}).get("score", ""),
        "amount_transform_score": plan_score.get("amount_transform", {}).get("score", ""),
        "row_score": row_score.get("score", ""),
        "overall_score": result["overall_score"],
    }
    write_header = not CSV_FILE.exists()
    CSV_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv_lib.DictWriter(f, fieldnames=CSV_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow(csv_row)
