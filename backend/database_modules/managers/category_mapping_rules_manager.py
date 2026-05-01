#!python3
from datetime import datetime
from typing import Optional

from pleasant_database import DatabaseFile, DatabaseManager

from backend.database_modules.managers.common import DB_FILE
from backend.database_modules.models.category_mapping_rules import CategoryMappingRulesTable

from pleasant_loggers import get_logger
logger = get_logger(__name__)


class CategoryMappingRulesManager(DatabaseManager):
    """
    Manager for the category_mapping_rules table.

    Stores two types of normalization rules built up from AI-assisted CSV imports:
      - Column rules: map a raw CSV header to a Budgy schema field name.
      - Category rules: map a raw CSV category string to a Budgy primary + detailed category.

    Rules are checked before calling the AI on each upload; only unmapped values are
    sent to Claude. Approved AI mappings are saved here so future uploads hit the cache.

    Methods:
        - get_column_rule: Return the schema field name for a raw header, or None.
        - get_category_rule: Return {primary, detailed} for a raw category string, or None.
        - upsert_column_rule: Create or update a column mapping rule.
        - upsert_category_rule: Create or update a category mapping rule.
        - list_rules: Return all rules.
    """

    def __init__(self, db_file: DatabaseFile):
        super().__init__(CategoryMappingRulesTable, db_file)

    def get_column_rule(self, raw_value: str) -> Optional[str]:
        """Return the mapped schema column name for a raw CSV header, or None if not found."""
        results = self.fetch_items_by_attribute(rule_type="column", raw_value=raw_value)
        if results:
            return results[0].mapped_column
        return None

    def get_category_rule(self, raw_value: str) -> Optional[dict]:
        """
        Return a dict with 'primary' and 'detailed' keys for a raw category string,
        or None if no rule exists.
        """
        results = self.fetch_items_by_attribute(rule_type="category", raw_value=raw_value)
        if results:
            rule = results[0]
            return {"primary": rule.primary_cat, "detailed": rule.detailed_cat}
        return None

    def upsert_column_rule(self, raw_value: str, mapped_column: str) -> CategoryMappingRulesTable:
        """
        Create or update the column mapping rule for raw_value.
        Returns the saved rule row.
        """
        existing = self.fetch_items_by_attribute(rule_type="column", raw_value=raw_value)
        if existing:
            self.update_item(existing[0].id, mapped_column=mapped_column)
            logger.info(f"Updated column rule: {raw_value!r} -> {mapped_column!r}")
            return self.fetch_item_by_id(existing[0].id)

        self.add_item(
            rule_type="column",
            raw_value=raw_value,
            mapped_column=mapped_column,
            primary_cat=None,
            detailed_cat=None,
            created_at=datetime.now(),
        )
        logger.info(f"Created column rule: {raw_value!r} -> {mapped_column!r}")
        return self.fetch_items_by_attribute(rule_type="column", raw_value=raw_value)[0]

    def upsert_category_rule(
        self, raw_value: str, primary_cat: str, detailed_cat: str
    ) -> CategoryMappingRulesTable:
        """
        Create or update the category mapping rule for raw_value.
        Returns the saved rule row.
        """
        existing = self.fetch_items_by_attribute(rule_type="category", raw_value=raw_value)
        if existing:
            self.update_item(existing[0].id, primary_cat=primary_cat, detailed_cat=detailed_cat)
            logger.info(f"Updated category rule: {raw_value!r} -> {primary_cat!r}/{detailed_cat!r}")
            return self.fetch_item_by_id(existing[0].id)

        self.add_item(
            rule_type="category",
            raw_value=raw_value,
            mapped_column=None,
            primary_cat=primary_cat,
            detailed_cat=detailed_cat,
            created_at=datetime.now(),
        )
        logger.info(f"Created category rule: {raw_value!r} -> {primary_cat!r}/{detailed_cat!r}")
        return self.fetch_items_by_attribute(rule_type="category", raw_value=raw_value)[0]

    def list_rules(self) -> list:
        """Return all rules."""
        return self.fetch_all_items()


category_mapping_rules_manager = CategoryMappingRulesManager(DB_FILE)
