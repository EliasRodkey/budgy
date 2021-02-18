#! python3
# controller.py - controls the interactions between the user and the 
# model backend

from view import View
from model import Model
from shelf.config import *
import shelve
import datetime


class Controller():
    def __init__(self):
        # model attributes
        self.get_last_budget()
        self.model = Model(self, LOC_TRANSACTION_PATH, ALL_CATEGORIES)
        self.csv = self.model.csv_data
        self.plotter = self.model.plotter
        self.avg_monthly_income = 2000

        # view and page attributes
        self.view = View(self)
        self.page_history = []

        # monthly_spending = self.csv.spending_breakdown(self.csv.months)
        # monthly_spending_plot = self.plotter(monthly_spending, ALL_CATEGORIES)
        # monthly_spending_plot.plot_all_categories()

        self.view.setup_ui()
        self.view.stackedWidget.setCurrentIndex(0)
        self.view.show_ui()

        self.past_budgets.close()
        
    def show_page(self, page):
        #code for new page to ensure current data displayed
        self.view.stackedWidget.setCurrentWidget(page)
        self.page_history.append(page)
    
    def show_last_page(self):
        last_page = self.page_history[-2]
        self.view.stackedWidget.setCurrentWidget(last_page)
        self.page_history.append(last_page)
    
    def get_last_budget(self):
        self.past_budgets = shelve.open(LOC_SHELF_PATH)
        try:
            past_budget_numbers = self.shelf_nums_from_keys(self.past_budgets)
            self.latest_budget_num = max(past_budget_numbers)
            self.latest_budget_key = f"budget_{self.latest_budget_num}"
        except ValueError: 
            self.latest_budget_num = 0
            self.latest_budget_key = f"budget_{self.latest_budget_num}"
            budget_dict = {}
            budget_dict["save_date"] = datetime.datetime.now().strftime("%m/%d/%Y")
            for category in list(ALL_CATEGORIES.keys()):
                budget_dict[category] = 0
            self.past_budgets[self.latest_budget_key] = budget_dict
        self.last_budget = self.past_budgets[self.latest_budget_key]
    
    def shelf_nums_from_keys(self, shelf):
        keys = list(shelf.keys())
        numbers = []
        for key in keys:
            numbers.append(int(key.split("budget_")[1]))
        return numbers

    def save_budget(self):
        budget_dict = {"save_date" : datetime.datetime.now().strftime("%m/%d/%Y")}
        for category in list(ALL_CATEGORIES.keys()):
            if category == "Income":
                continue
            else:
                value = self.view.budget_edit_page.percent_dict[category].text().replace("%", "")
                budget_dict[category] = int(value)
        self.latest_budget_num += 1
        self.latest_budget_key = f"budget_{self.latest_budget_num}"
        self.past_budgets[self.latest_budget_key] = budget_dict
        self.last_budget = self.past_budgets[self.latest_budget_key]
             
            
if __name__ == "__main__":
    app = Controller()