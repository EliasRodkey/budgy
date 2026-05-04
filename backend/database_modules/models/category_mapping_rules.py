#!python3
from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint
from pleasant_database import BaseTable


class CategoryMappingRulesTable(BaseTable):
    """
    Stores rules that normalize raw CSV headers and category strings to Budgy's schema.

    Two rule types:
      - 'column': maps a raw CSV header (raw_value) to a schema field name (mapped_column)
      - 'category': maps a raw category string (raw_value) to primary_cat + detailed_cat

    Database Structure:
        table name: category_mapping_rules
    Columns:
        - id: Integer, Primary Key
        - rule_type: 'column' | 'category'
        - raw_value: the original header or category string from the CSV
        - mapped_column: schema field name (column rules only, nullable)
        - primary_cat: Budgy primary category (category rules only, nullable)
        - detailed_cat: Budgy detailed category (category rules only, nullable)
        - created_at: DateTime
    Constraints:
        - UNIQUE (rule_type, raw_value) — one rule per raw value per type
    """

    __tablename__ = "category_mapping_rules"

    __table_args__ = (
        UniqueConstraint("rule_type", "raw_value", name="uq_category_mapping_rule"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_type = Column(String, nullable=False)  # 'column' or 'category'
    raw_value = Column(String, nullable=False)
    mapped_column = Column(String, nullable=True)
    primary_cat = Column(String, nullable=True)
    detailed_cat = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
