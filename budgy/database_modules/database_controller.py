#!python3
"""
"""
# Standard library imports
import os

# Third party imports

# Custom imports
from pleasant_database import DatabaseFile

# Local imports
from budgy.utils.analysis_utils import CategoriesEnum
from .managers.budget_manager import BudgetsTableManager
from .managers.summary_manager import SummariesTableManager
from .managers.transaction_manager import TransactionsTableManager, UpdatesTableManager

# initialize module logger
import logging
logger = logging.getLogger(__name__)



class DatabaseController:
    """

    Methods:
        - Performs a mass upload to summaries table by iterating over all month / year pairs found in transactions table.
    """
    def __init__(self, db_file: DatabaseFile):
        """"""
        self.updates_manager = UpdatesTableManager(db_file)
        self.transactions_manager = TransactionsTableManager(db_file, self.updates_manager)
        self.summaries_manager = SummariesTableManager(db_file)
        self.budgets_manager = BudgetsTableManager(db_file)
    
    # Update a summary based on an updated value in the csv upload
    def upload_transactions_and_update_summary(self, csv_filepath) -> None:
        """"""
        logger.info(f"Uploading csv: {os.path.basename(csv_filepath)} and updating summaries table.")

        updates_items = self.transactions_manager.upload_csv(csv_filepath)
        month_year_pairs = set((item.authorized_date.month, item.authorized_date.year) for item in updates_items)

        for month, year in month_year_pairs:
            summary = self.transactions_manager.generate_monthly_category_report(month, year)
            self.summaries_manager.update_summary(month, year, summary)

    # Create all summaries from time periods present in the transactions database
    def initialize_summaries(self) -> None:
        """Performs a mass upload to summaries table by iterating over all month / year pairs found in transactions table."""
        logger.info(f"Initializing summaries table bulk upload")

        month_year_pairs = set(self.transactions_manager.fetch_month_year_pairs())

        for month, year in month_year_pairs:
            summary = self.transactions_manager.generate_monthly_category_report(month, year)
            self.summaries_manager.upload_monthly_summary(month, year, summary)

    # TODO: Add a is_empty to DatabaseManager class in pleasant_database
    def initialize_budgets(self) -> None:
        """"""
        pass

    # Should do an initial scan of the uploads folder
    # NOTE: Eventually when we upload a CSV file from the front end, we will have to make sure that is gets loaded into the proper local directory as a csv file.
    def initialize_transactions(self) -> None:
        """"""
        pass

    # Calculate average category spending based on category counts and summary
    def calculate_average_category_spending(self, category) -> dict:
        """"""
        pass

    # Calculate total category spending based on category counts and summary
    def calculate_total_category_spending(self, category) -> dict:
        """"""
        pass

    # Calulate percentages per category of summary / budget spending

    # Calculate remaining budget per category per month / year

    # Calulate average over / under budget

    # Calculate total debt to budget

    # Rank categories based on their spending relative to budgeted amount

    # TODO: Move to utils
    def _one_dimensional_df_to_dict() -> dict:
        """"""
        pass
    