#!python3
from datetime import datetime, timezone

from pleasant_database import DatabaseFile, DatabaseManager

from ..models.dirty_months import DirtyMonthsTable

from pleasant_loggers import get_logger
logger = get_logger(__name__)


class DirtyMonthsManager(DatabaseManager):
    """
    Manager for the dirty_months queue table.
    Tracks months whose summary aggregates are stale due to transaction edits.
    """
    def __init__(self, db_file: DatabaseFile):
        super().__init__(DirtyMonthsTable, db_file)

    def mark_dirty(self, month: int, year: int) -> None:
        """Inserts or updates a dirty-month record. Safe to call multiple times."""
        self.upsert({"month": month, "year": year}, marked_at=datetime.now(timezone.utc))

    def get_all_dirty(self) -> list[tuple[int, int]]:
        """Returns list of (month, year) tuples for all dirty months."""
        rows = self.fetch_all_items()
        return [(row.month, row.year) for row in rows]

    def any_dirty(self) -> bool:
        """Returns True if any dirty months are queued."""
        return self.count_items() > 0

    def clear(self, month: int, year: int) -> None:
        """Removes the dirty-month record after recompute completes."""
        self.delete_items_by_attribute(month=month, year=year)
