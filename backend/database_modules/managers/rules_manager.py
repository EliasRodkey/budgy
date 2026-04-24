#!python3
"""
backend.database_modules.managers.rules_manager.py -
Manager for the transaction_rules table.

Classes:
    - TransactionRulesManager: CRUD manager for TransactionRulesTable.

Module-level instance:
    - rules_manager: Shared RulesManager using the production DB_FILE.
"""
# Standard library imports
from datetime import datetime
from typing import List, Optional

# Custom imports
from pleasant_database import DatabaseFile, DatabaseManager, DatabaseIntegrityError

# Local imports
from backend.database_modules.managers.common import DB_FILE
from backend.database_modules.models.rules import TransactionRulesTable

from pleasant_loggers import get_logger
logger = get_logger(__name__)


class TransactionRulesManager(DatabaseManager):
    """
    Manager for the transaction_rules table.

    Methods:
        - upsert_rule: Create or update a rule for a (description, account_name) pair.
        - get_rule: Retrieve a rule by description + account_name, or None.
        - list_rules: Return all rules.
        - update_rule: Update specific fields on an existing rule by id.
        - delete_rule: Delete a rule by id.
        - apply_rules_to_transaction: Stub — will apply matching rule to a single transaction.
        - apply_rules_to_all: Stub — will apply all rules to all transactions (called after CSV import).
    """

    def __init__(self, db_file: DatabaseFile):
        super().__init__(TransactionRulesTable, db_file)

    def upsert_rule(
        self,
        match_description: str,
        match_account_name: str,
        primary_category: Optional[str] = None,
        detailed_category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> TransactionRulesTable:
        """
        Create a new rule or update an existing one for the given
        (match_description, match_account_name) pair.

        Args:
            match_description: Exact description string to match.
            match_account_name: Exact account_name string to match.
            primary_category: Primary category to apply (optional).
            detailed_category: Detailed category to apply (optional).
            tags: List of tag strings to apply (optional). Stored as comma-separated string.

        Returns:
            The created or updated TransactionRulesTable row.
        """
        now = datetime.now()
        tags_str = ",".join(tags) if tags else None

        existing = self.get_rule(match_description, match_account_name)
        if existing:
            updates: dict = {"updated_at": now}
            if primary_category is not None:
                updates["primary_category"] = primary_category
            if detailed_category is not None:
                updates["detailed_category"] = detailed_category
            if tags is not None:
                updates["tags"] = tags_str
            self.update_item(existing.id, **updates)
            logger.info(f"Updated rule id={existing.id} for ({match_description!r}, {match_account_name!r})")
            return self.get_rule(match_description, match_account_name)

        self.add_item(
            match_description=match_description,
            match_account_name=match_account_name,
            match_type="exact",
            primary_category=primary_category,
            detailed_category=detailed_category,
            tags=tags_str,
            created_at=now,
            updated_at=now,
        )
        logger.info(f"Created rule for ({match_description!r}, {match_account_name!r})")
        return self.get_rule(match_description, match_account_name)

    def get_rule(
        self, match_description: str, match_account_name: str
    ) -> Optional[TransactionRulesTable]:
        """Return the rule for the given description + account_name, or None."""
        results = self.fetch_items_by_attribute(match_description=match_description)
        for rule in results:
            if rule.match_account_name == match_account_name:
                return rule
        return None

    def list_rules(self) -> List[TransactionRulesTable]:
        """Return all rules ordered by created_at descending."""
        return self.fetch_all_items()

    def update_rule(self, rule_id: int, **kwargs) -> TransactionRulesTable:
        """
        Update specific fields on a rule by id.
        Automatically sets updated_at to now.
        """
        kwargs["updated_at"] = datetime.now()
        if "tags" in kwargs and isinstance(kwargs["tags"], list):
            kwargs["tags"] = ",".join(kwargs["tags"]) if kwargs["tags"] else None
        self.update_item(rule_id, **kwargs)
        return self.fetch_item_by_id(rule_id)

    def delete_rule(self, rule_id: int) -> None:
        """Delete a rule by id."""
        self.delete_item(rule_id)
        logger.info(f"Deleted rule id={rule_id}")

    def apply_rules_to_transaction(self, transaction_id: int) -> None:
        """
        Stub: Apply any matching rule to a single transaction.
        Will look up the transaction's description + account_name, find a matching rule,
        and update the transaction's category/tags accordingly.
        Not yet implemented — placeholder for future CSV upload pipeline integration.
        """
        logger.info(f"[STUB] apply_rules_to_transaction called for transaction_id={transaction_id}")

    def apply_rules_to_all(self) -> None:
        """
        Stub: Apply all rules to all transactions in the database.
        Called after each CSV import to auto-categorize/tag new transactions.
        Not yet implemented — placeholder for future CSV upload pipeline integration.
        """
        logger.info("[STUB] apply_rules_to_all called — no-op for now")


rules_manager = TransactionRulesManager(DB_FILE)
