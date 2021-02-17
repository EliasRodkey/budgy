#! python3
# controller.py - controls the interactions between the user and the 
# model backend

from view import View
from model import Model
from shelf.config import ALL_CATEGORIES, LOC_TRANSACTION_PATH


class Controller():
    def __init__(self):
        # view and page attributes
        self.view = View(self)
        self.page_history = []

        # model attributes
        self.model = Model(self, LOC_TRANSACTION_PATH, ALL_CATEGORIES)
        self.csv = self.model.csv_data
        self.plotter = self.model.plotter

        # monthly_spending = self.csv.spending_breakdown(self.csv.months)
        # monthly_spending_plot = self.plotter(monthly_spending, ALL_CATEGORIES)
        # monthly_spending_plot.plot_all_categories()

        self.view.setup_ui()
        self.view.stackedWidget.setCurrentIndex(0)
        self.view.show_ui()
    
    def show_page(self, page):
        #code for new page to ensure current data displayed
        self.view.stackedWidget.setCurrentWidget(page)
        self.page_history.append(page)

        

if __name__ == "__main__":
    app = Controller()