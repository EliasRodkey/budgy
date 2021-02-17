#! python3
# controller.py - controls the interactions between the user and the 
# model backend

from view import View
from model import Model
from shelf.config import ALL_CATEGORIES, LOC_TRANSACTION_PATH


class Controller():
    def __init__(self):
        self.view = View(self)
        self.model = Model(self, LOC_TRANSACTION_PATH, ALL_CATEGORIES)
        self.csv = self.model.csv_data
        self.plotter = self.model.plotter

        # monthly_spending = self.csv.spending_breakdown(self.csv.months)
        # monthly_spending_plot = self.plotter(monthly_spending, ALL_CATEGORIES)
        # monthly_spending_plot.plot_all_categories()

        self.view.setup_ui()
        self.view.stackedWidget.setCurrentIndex(0)
        self.view.show_ui()

        

if __name__ == "__main__":
    app = Controller()