#! python3
# controller.py - controls the interactions between the user and the 
# model backend

from pandas.core.base import DataError
from view import View
from model import Model
from shelf.config import Config
import shelve
import datetime


class Controller():
    # TODO: make save budget stuff
    def __init__(self):
        # bring configuration setting into controller
        self.config = Config()

        # model attributes
        self.get_last_budget()
        self.model = Model(self, self.config.LOC_TRANSACTION_PATH, self.config.ALL_CATEGORIES)
        self.plotter = self.model.plotter
        self.avg_monthly_income = self.find_avg_monthly_income()
        self.search_column = "General Category"

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
        for category in list(self.config.ALL_CATEGORIES.keys()):
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
            self, self.model.df, 
            "Actual Spending ($)", 
            "General Category", 
            row_ids,
            ["Income"], 1,
            None, False
        ).data_frame
        decay_value = 0
        wavg = 0
        for i, row_id in enumerate(row_ids):
            income = incomes[incomes["Row ID"] == row_id]["Income"].item()
            weight = single_weight * decay_value
            wavg += income * weight
            decay_value += 1
        return round(wavg, 2)
    
    ### Combobox and Checkbox methods ###
    def input_changed(self, choice):
        if choice == "":
            return
        sender = self.view.spending_analysis_page.sender()
        sender_name = sender.objectName()
        analysis_page = self.view.spending_analysis_page
        if sender_name == "data_display_type_combobox":
            analysis_page.update_combobox(
                analysis_page.chart_type_comboBox,
                self.config.ANALYSIS_CHART_MAP[choice]
            )
            analysis_page.chart_type_comboBox.setCurrentIndex(0)
        elif sender_name == "chart_type_combobox":
            analysis_page.update_combobox(
                analysis_page.time_period_combobox,
                self.config.CHART_BREAKDOWN_MAP[choice]
            )
        elif sender_name == "time_period_combox":
            pass
        elif sender_name == "sub_category_combobox":
            pass
        elif sender_name == "category_combobox":
            pass

    def sub_category_checked(self, state):
        general_category_analysis = list(self.config.ANALYSIS_CHART_MAP.keys())
        sub_category_incomp = [
            "Net Income", 
            "Budget Side by Side ($)", 
            "Budget Side by Side (%)", 
            "Amount Over/Under Budget ($)", 
            "Amount Over/Under Budget (%)",
            "Income Side by Side",
            "Budgeted Spending ($)",
            "Budgeted Spending (%)",
            "Over Budget (T/F)"
        ]
        analysis_page = self.view.spending_analysis_page
        if state == 2:
            self.search_column = "Category"
            self.view.spending_analysis_page.change_subcategory_combobox(state)
            for item in sub_category_incomp:
                general_category_analysis.remove(item)
            analysis_page.data_display_type_comboBox.clear()
            analysis_page.data_display_type_comboBox.addItems(general_category_analysis)
        else:
            self.search_column = "General Category"
            self.view.spending_analysis_page.change_subcategory_combobox(state)
            analysis_page.data_display_type_comboBox.clear()
            analysis_page.data_display_type_comboBox.addItems(general_category_analysis)

    ### Analysis Methods ###
    def analyze_spending(self):
        inputs, chart = self.retrieve_inputs()
        if inputs == None:
            return
        table = self.model.table_maker(
            **inputs,
        ).data_frame
        breakdown = self.view.spending_analysis_page.time_period_combobox.currentText()
        if type(table) == dict:
            for category in table:
                plot = self.plotter(
                    table[category], chart,
                    breakdown,
                    inputs["search_column"]
                )
                plot.show()
        else:
            plot = self.plotter(
                table, chart, 
                breakdown, 
                inputs["search_column"]
            )
            plot.show()
    
    ### Input Retrieval Methods ###
    def retrieve_inputs(self):
        analysis_page = self.view.spending_analysis_page
        analysis_type = analysis_page.data_display_type_comboBox.currentText()
        category_list = self.get_category_list()
        dates_list = self.get_date_list()
        chart = analysis_page.chart_type_comboBox.currentText()
        comparison = False
        if chart == "Comparison Chart":
            comparison = True
        if self.search_column == "Category":
            budget = None
        else:
            budget = self.last_budget

        inputs = {
            "controller" : self,
            "df" : self.model.df,
            "analysis_type" : analysis_type,
            "search_column" : self.search_column,
            "date_range_list" : dates_list,
            "category_list" : category_list, 
            "avg_monthly_income" : self.avg_monthly_income,
            "budget" : budget,
            "comparison" : comparison
        }
        error, msg = self.check_input_error(inputs)
        if error:
            self.view.error_popup(msg)
            return None, None
        return inputs, chart

    def get_category_list(self):
        analysis_page = self.view.spending_analysis_page
        if self.search_column == "Category":
            choice = analysis_page.sub_category_combobox.currentText()
            category_list = self.config.ALL_CATEGORIES[choice]
        else:
            choices = analysis_page.category_combobox.checkedItems()
            category_list = choices
        return category_list

    def get_date_list(self):
        start = self.view.spending_analysis_page.start_date.date().toPyDate()
        end = self.view.spending_analysis_page.end_date.date().toPyDate()
        self.dates_obj = self.model.date_ranges(start, end)
        breakdown = self.view.spending_analysis_page.time_period_combobox.currentText()
        if breakdown == "All":
            dates_list = self.dates_obj.all
        elif breakdown == "Years":
            dates_list = self.dates_obj.years
        elif breakdown == "Months":
            dates_list = self.dates_obj.months
        elif breakdown == "Weeks":
            dates_list = self.dates_obj.weeks
        else:
            dates_list = self.dates_obj.all
        return dates_list

    ### Error Handling Methods ###
    def check_input_error(self, inputs):
        error = False
        msg = ""
        if len(inputs["category_list"]) == 0:
            if inputs["analysis_type"] != "Net Income" and \
            inputs["analysis_type"] != "Income Side by Side":
                error = True
                msg = "No Categories Chosen\nPlease Select at Least One"
        return error, msg
            
if __name__ == "__main__":
    app = Controller()