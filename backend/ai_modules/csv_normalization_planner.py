#!python3
from backend.ai_modules.ai_client_service import (
    AIClientService,
    ALL_SCHEMA_FIELDS,
    REQUIRED_SCHEMA_FIELDS,
)
from backend.ai_modules.normalization_plan import AmountTransform, CategoryMapping, NormalizationPlan
from backend.database_modules.managers.category_mapping_rules_manager import CategoryMappingRulesManager

from pleasant_loggers import get_logger
logger = get_logger(__name__)

_ALL_SCHEMA_FIELD_SET = set(ALL_SCHEMA_FIELDS)
_REQUIRED_FIELD_SET = set(REQUIRED_SCHEMA_FIELDS)


class CSVNormalizationPlanner:
    """
    Orchestrates CSV normalization by checking the rules cache before calling the AI.

    Processing order:
      1. Look up each header and category value in the rules cache.
      2. If all required fields are covered by cache + exact header matches, and
         all categories are cached → return plan with zero AI calls.
      3. For any uncached headers or categories, call AIClientService with only
         those items.
      4. Merge cached rules and AI results into a final NormalizationPlan.

    Has no side effects — does not save rules. Rule saving happens separately
    when the user approves the plan.
    """

    def __init__(
        self,
        rules_manager: CategoryMappingRulesManager,
        ai_service: AIClientService,
    ):
        self._rules = rules_manager
        self._ai = ai_service

    def plan(
        self,
        headers: list[str],
        unique_categories: list[str],
    ) -> tuple[NormalizationPlan, bool]:
        """
        Produce a NormalizationPlan for the given CSV headers and category values.

        Args:
            headers: Raw column header strings from the CSV.
            unique_categories: Unique category values found in the CSV.

        Returns:
            Tuple of (NormalizationPlan, used_cache) where used_cache is True when
            all mappings came from the rules cache and no AI call was made.
        """
        # 1. Check rules cache for all headers and categories
        cached_col_rules: dict[str, str] = {}
        for h in headers:
            rule = self._rules.get_column_rule(h)
            if rule is not None:
                cached_col_rules[h] = rule

        cached_cat_rules: dict[str, dict] = {}
        for c in unique_categories:
            rule = self._rules.get_category_rule(c)
            if rule is not None:
                cached_cat_rules[c] = rule

        # 2. Find items not covered by cache or exact schema field match
        uncached_headers = [
            h for h in headers
            if h not in cached_col_rules and h not in _ALL_SCHEMA_FIELD_SET
        ]
        uncached_categories = [
            c for c in unique_categories if c not in cached_cat_rules
        ]

        # 3. Call AI only for uncached items, or skip entirely on pure cache hit
        if uncached_headers or uncached_categories:
            logger.info(
                f"Cache miss: sending {len(uncached_headers)} headers and "
                f"{len(uncached_categories)} categories to AI"
            )
            ai_plan = self._ai.plan_csv(uncached_headers, uncached_categories)
            merged_column_map = {**cached_col_rules, **ai_plan.column_map}
            merged_category_map = {
                **{k: CategoryMapping(primary=v["primary"], detailed=v["detailed"])
                   for k, v in cached_cat_rules.items()},
                **ai_plan.category_map,
            }
            amount_transform = ai_plan.amount_transform
            debit_column = ai_plan.debit_column
            credit_column = ai_plan.credit_column
            issues = ai_plan.issues
            column_map_reasoning = ai_plan.column_map_reasoning
            category_map_reasoning = ai_plan.category_map_reasoning
            amount_transform_reasoning = ai_plan.amount_transform_reasoning
            used_cache = False
        else:
            logger.info("Full cache hit: returning plan without AI call")
            merged_column_map = dict(cached_col_rules)
            merged_category_map = {
                k: CategoryMapping(primary=v["primary"], detailed=v["detailed"])
                for k, v in cached_cat_rules.items()
            }
            amount_transform = AmountTransform.EXPENSE_NEGATIVE
            debit_column = None
            credit_column = None
            issues = []
            column_map_reasoning = None
            category_map_reasoning = None
            amount_transform_reasoning = None
            used_cache = True

        # 4. Strip identity mappings — headers already named as schema fields
        #    need no entry in column_map (the transform applicator passes them through)
        final_column_map = {
            k: v for k, v in merged_column_map.items()
            if k not in _ALL_SCHEMA_FIELD_SET
        }

        # 5. Determine which required fields are reachable after merging
        covered_fields = set(v for v in final_column_map.values() if v is not None)
        covered_fields |= {h for h in headers if h in _ALL_SCHEMA_FIELD_SET}
        unmapped_required = [f for f in REQUIRED_SCHEMA_FIELDS if f not in covered_fields]

        plan = NormalizationPlan(
            column_map=final_column_map,
            category_map=merged_category_map,
            amount_transform=amount_transform,
            debit_column=debit_column,
            credit_column=credit_column,
            issues=issues,
            unmapped_required_columns=unmapped_required,
            column_map_reasoning=column_map_reasoning,
            category_map_reasoning=category_map_reasoning,
            amount_transform_reasoning=amount_transform_reasoning,
        )
        return plan, used_cache
