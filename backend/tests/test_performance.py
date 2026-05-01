#!python3
"""
tests.test_performance.py

Performance timing tests for key budgy operations.
These tests do not assert thresholds — they log elapsed time so you can observe
how long each operation takes as the codebase evolves.

Run with: pytest tests/test_performance.py -v -s
"""
# Standard library imports
import time

# Third party imports
import pytest

# Local imports
from backend.tests.conftest import (
    full_transactions_database,
    full_summaries_database,
    clean_summaries_database,
    clean_budgets_database,
)

# Initialize module logger
from pleasant_loggers import get_logger
logger = get_logger(__name__)


# ─── TransactionsTableManager ────────────────────────────────────────────────

def test_generate_monthly_summary_speed(full_transactions_database):
    """Log per-run and average elapsed time for generate_monthly_summary over 10 iterations."""
    times = []
    for i in range(10):
        start = time.time()
        full_transactions_database.generate_monthly_summary(12, 2025)
        elapsed = time.time() - start
        times.append(elapsed)
        logger.info(f"  Run {i + 1:>2}: generate_monthly_summary took {elapsed:.6f}s")
    avg = sum(times) / len(times)
    logger.info(f"  Average over 10 runs: {avg:.6f}s")
    print(f"\n[PERF] generate_monthly_summary — avg {avg:.4f}s over 10 runs")


# ─── SummariesTableManager ────────────────────────────────────────────────────

def test_fetch_summaries_over_period_speed(full_summaries_database):
    """Log per-run and average elapsed time for fetch_summaries_over_period over 10 iterations.

    Useful for observing query cost on the wide 411-column summaries table.
    """
    summaries_manager, _ = full_summaries_database
    times = []
    for i in range(10):
        start = time.time()
        summaries_manager.fetch_summaries_over_period(12, 2025)
        elapsed = time.time() - start
        times.append(elapsed)
        logger.info(f"  Run {i + 1:>2}: fetch_summaries_over_period took {elapsed:.6f}s")
    avg = sum(times) / len(times)
    logger.info(f"  Average over 10 runs: {avg:.6f}s")
    print(f"\n[PERF] fetch_summaries_over_period — avg {avg:.4f}s over 10 runs")


# ─── End-to-end pipeline ─────────────────────────────────────────────────────

def test_full_upload_and_summarize_pipeline_speed(clean_summaries_database, full_transactions_database):
    """Log total elapsed time for uploading a monthly summary for every month/year pair in the transactions DB.

    Covers: generate_monthly_summary → upload_monthly_summary for all available months.
    """
    summaries_manager, _ = clean_summaries_database
    month_year_pairs = full_transactions_database.retrieve_month_year_pairs()

    start = time.time()
    for month, year in month_year_pairs:
        summary = full_transactions_database.generate_monthly_summary(month, year)
        summaries_manager.upload_monthly_summary(month, year, summary, budget_id=1)
    elapsed = time.time() - start

    logger.info(
        f"Full pipeline ({len(month_year_pairs)} months): "
        f"generate + upload_monthly_summary took {elapsed:.4f}s total "
        f"({elapsed / max(len(month_year_pairs), 1):.4f}s per month)"
    )
    print(
        f"\n[PERF] Full upload+summarize pipeline — {elapsed:.4f}s total "
        f"for {len(month_year_pairs)} months "
        f"({elapsed / max(len(month_year_pairs), 1):.4f}s/month)"
    )
