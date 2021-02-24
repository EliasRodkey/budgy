#! python3
# controller.py - controls the interactions between the user and the 
# model backend

from numpy.testing._private.utils import decorate_methods
from view import View
from model import Model
from shelf.config import Config
import shelve
import datetime


class Controller():
    def __init__(self):
        # bring configuration setting into controller
        self.config = Config()
        
        # model attributes
        self.get_last_budget()
        self.model = Model(self, self.config.LOC_TRANSACTION_PATH, self.config.ALL_CATEGORIES)
        self.plotter = self.model.plotter
        self.avg_monthly_income = self.find_avg_monthly_income()

        # view and page attributes
        self.view = View(self)
        self.page_history = []

        # view loading and showing
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
        self.past_budgets = shelve.open(self.config.LOC_SHELF_PATH)
        try:
            past_budget_numbers = self.shelf_nums_from_keys(self.past_budgets)
            self.latest_budget_num = max(past_budget_numbers)
            self.latest_budget_key = f"budget_{self.latest_budget_num}"
        except ValueError: 
            self.latest_budget_num = 0
            self.latest_budget_key = f"budget_{self.latest_budget_num}"
            budget_dict = {}
            budget_dict["save_date"] = datetime.datetime.now().strftime("%m/%d/%Y")
            for category in list(self.config.ALL_CATEGORIES.keys()):
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
    
    def find_avg_monthly_income(self):
        single_weight = 100 / 78 / 100
        self.dates = self.model.date_ranges(self.model.start, self.model.end)
        one_year_dates = self.dates.find_month_from_today(12)[0]
        split = one_year_dates.split(" - ")
        row_ids = self.model.date_ranges(
            datetime.datetime.strptime(split[0], "%m/%d/%Y"), 
            datetime.datetime.strptime(split[1], "%m/%d/%Y")
        ).months
        incomes = self.model.table_maker(
            self.model.df, "actual_spending", 
            "General Category", 
            row_ids,
            ["Income"], 1
        ).data_frame
        decay_value = 0
        wavg = 0
        for i, row_id in enumerate(row_ids):
            income = incomes[incomes["Row ID"] == row_id]["Income"].item()
            weight = single_weight * decay_value
            wavg += income * weight
            decay_value += 1
        return round(wavg, 2)

            

if __name__ == "__main__":
    app = Controller()