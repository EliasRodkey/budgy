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
        - apply_rules_to_transaction: Apply the matching rule (if any) to a single transaction.
        - apply_rules_to_all: Apply all rules to all matching transactions (called after CSV import).
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
        exclude: Optional[bool] = None,
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
            exclude: If set, matching transactions will be marked excluded (True) or included (False).

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
            if exclude is not None:
                updates["exclude"] = exclude
            self.update_item(existing.id, **updates)
            logger.info(f"Updated rule id={existing.id} for ({match_description!r}, {match_account_name!r})")
            return self.get_rule(match_description, match_account_name)

        item_kwargs: dict = dict(
            match_description=match_description,
            match_account_name=match_account_name,
            match_type="exact",
            primary_category=primary_category,
            detailed_category=detailed_category,
            tags=tags_str,
            created_at=now,
            updated_at=now,
        )
        if exclude is not None:
            item_kwargs["exclude"] = exclude
        self.add_item(**item_kwargs)
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

    def apply_rules_to_transaction(self, transaction_id: int, tx_mgr) -> bool:
        """
        Apply the matching rule (if any) to a single transaction.

        Args:
            transaction_id: ID of the transaction to update.
            tx_mgr: TransactionsTableManager instance for querying and updating the transaction.

        Returns:
            True if a category field (primary_category or detailed_category) was changed.
        """
        tx = tx_mgr.fetch_item_by_id(transaction_id)
        if tx is None:
            logger.warning(f"apply_rules_to_transaction: transaction {transaction_id} not found")
            return False

        rule = self.get_rule(tx.description, tx.account_name)
        if rule is None:
            return False

        col_updates: dict = {}
        if rule.primary_category:
            col_updates["primary_category"] = rule.primary_category
        if rule.detailed_category:
            col_updates["detailed_category"] = rule.detailed_category
        if rule.tags:
            existing = [t for t in (tx.tags or "").split(",") if t]
            rule_tags = [t.strip() for t in rule.tags.split(",") if t.strip()]
            col_updates["tags"] = ",".join(dict.fromkeys(existing + rule_tags))
        if rule.exclude is not None:
            col_updates["exclude"] = rule.exclude

        if not col_updates:
            return False

        tx_mgr.update_item(transaction_id, **col_updates)
        logger.info(f"Applied rule to transaction {transaction_id}: {col_updates}")
        return "primary_category" in col_updates or "detailed_category" in col_updates

    def apply_rules_to_all(self, tx_mgr) -> list:
        """
        Apply all rules to all matching transactions.
        Called after each CSV import to auto-categorize/tag/exclude new transactions.

        Args:
            tx_mgr: TransactionsTableManager instance for querying and updating transactions.

        Returns:
            List of (month, year) tuples for months where category changes occurred.
        """
        rules = self.list_rules()
        if not rules:
            return []

        affected_months: set = set()
        for rule in rules:
            result = tx_mgr.query(
                columns=tx_mgr.return_columns,
                filters={
                    "description": ("==", rule.match_description),
                    "account_name": ("==", rule.match_account_name),
                },
            )
            for row in result.data.to_dict(orient="records"):
                col_updates: dict = {}
                if rule.primary_category:
                    col_updates["primary_category"] = rule.primary_category
                if rule.detailed_category:
                    col_updates["detailed_category"] = rule.detailed_category
                if rule.tags:
                    existing = [t for t in (row.get("tags") or "").split(",") if t]
                    rule_tags = [t.strip() for t in rule.tags.split(",") if t.strip()]
                    col_updates["tags"] = ",".join(dict.fromkeys(existing + rule_tags))
                if rule.exclude is not None:
                    col_updates["exclude"] = rule.exclude

                if col_updates:
                    tx_mgr.update_item(row["id"], **col_updates)
                    if "primary_category" in col_updates or "detailed_category" in col_updates:
                        date = row.get("authorized_date")
                        if date is not None:
                            affected_months.add((date.month, date.year))

        logger.info(f"apply_rules_to_all: applied {len(rules)} rules, {len(affected_months)} months affected")
        return list(affected_months)


rules_manager = TransactionRulesManager(DB_FILE)
