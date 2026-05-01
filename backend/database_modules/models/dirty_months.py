#!python3
from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, UniqueConstraint
from pleasant_database import BaseTable


class DirtyMonthsTable(BaseTable):
    """
    Queue of months whose summary aggregates are stale due to transaction edits.
    Rows are inserted when a transaction's category or date is changed, and deleted
    after the summary for that month has been recomputed.
    """
    __tablename__ = "dirty_months"

    id = Column(Integer, primary_key=True, autoincrement=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    marked_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("month", "year", name="uq_dirty_month"),)
