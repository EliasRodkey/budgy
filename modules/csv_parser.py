#! python3
# csv_parser.py - reads and sorts data from raw mint csv
# using pandas dataframe
import logging

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)

import pandas as pd
import datetime

def range_to_datetimes(date_range):
    rang = date_range.split(" - ")
    old_date = datetime.datetime.strptime(rang[0], "%m/%d/%Y")
    new_date = datetime.datetime.strptime(rang[1], "%m/%d/%Y")
    return {"start" : old_date, "end" : new_date}


class CSVAnalyzer():
    def __init__(self, local_path, category_breakdown):
        self.ALL_CATEGORIES = category_breakdown
        self.local_path = local_path
        self.df = pd.read_csv(self.local_path)
        self.clean_df()
        
    def clean_df(self):
        for i, series in self.df.iterrows():
            if series["Transaction Type"] == "debit": #changes debits to negative numbers
                self.df.loc[i, "Amount"] = -self.df.loc[i, "Amount"]
        self.df.drop(columns = ["Transaction Type"], inplace = True)
        self.df['Date'] =  pd.to_datetime(self.df['Date'], format="%m/%d/%Y")
        self.df = self.create_umbrella_column(self.df)

    # creates an extra column with the more general spending category for each transaction
    def create_umbrella_column(self, df):
        # Add last column to df based on category
        umbrella_category = [] 
        # Iterates through the dataframe and matches each category with 
        # its umbrella counterpart
        for i, series in df.iterrows():
            for key in self.ALL_CATEGORIES.keys():
                if series["Category"] in self.ALL_CATEGORIES[key]:
                    umbrella_category.append(key)
            try:
                umbrella_category[i]
            except IndexError:
                umbrella_category.append(None)
        df["General Category"] = umbrella_category
        return df
    
    # opens tkinter file selectino dialog window
    def update_csv_file(self):
        import tkinter as tk
        from tkinter import filedialog as fd
        root = tk.Tk()
        root.withdraw()
        filename = fd.askopenfilename()
        self.df = pd.read_csv(filename)
        self.df.to_csv(self.local_path, index=False)
        self.__init__(self.local_path, self.ALL_CATEGORIES)


class DataPointConstructor():
    # gathers all transactions surrounding a single category
    # in a given timespan and adds them up returning the sum
    def __init__(
        self, df,
        analysis_type, 
        category, 
        search_column, 
        avg_monthly_income, 
        date_range,
        budget_percent=None
    ):
        self.df = df
        self.category = category
        self.avg_monthly_income = avg_monthly_income
        self.subcategory = True if search_column == "Category" else False
        self.date_range = range_to_datetimes(date_range)
        self.start_date = self.date_range["start"]
        self.end_date = self.date_range["end"]
        self.row_id = date_range
        self.days = self.end_date - self.start_date
        # filters whoel df for transactions between the start and end dates in the 
        # correct category
        self.filt = (self.df["Date"] >= self.start_date) \
            & (self.df["Date"] <= self.end_date) \
            & (self.df[search_column] == category)
        # expected income assessment
        if budget_percent != None:
            self.has_budget = budget_percent
        else:
            self.has_budget = False
        
        self.ANALYSIS_TYPES = {
            "actual_spending" : self.get_actual_spending,
            "actual_spending_percent" : self.get_actual_spending_percent,
            # "transactions" : self.get_transactions,
            "transaction_number" : self.get_number_transactions,
            "expected_income" : self.get_expected_income,
            "expected_spending_percent" : self.get_expected_spending_percent,
            "expected_spending" : self.get_expected_spending,
            "over_budget" : self.get_over_budget,
            "net_income" : self.get_actual_spending,
            "budget_comparison" : self.skip,
            "budget_comparison_percent" : self.skip,
            "income_comparison" : self.skip,
            "amount_over" : self.get_amount_over_expected,
            "amount_over_percent" : self.get_amount_over_expected_percent
        }
        self.actual_spending = self.get_actual_spending(self.df, self.filt)

        # create dataframe object for datapaoint
        self.point_df = self.point_to_df(analysis_type)

    def skip(self, df, filt):
        pass

    ### calculation methods ###
    def get_transactions(self, df, filt):
        transactions = df[filt]
        return transactions
    
    def get_number_transactions(self, df, filt):
        transactions = self.get_transactions(df, filt)
        num = len(transactions.index) 
        return num

    def get_actual_spending(self, df, filt):
        transactions = self.get_transactions(df, filt) 
        actual_spending = transactions["Amount"].sum()
        return round(actual_spending, 2)
    
    def get_expected_income(self, df, filt):
        return round((self.avg_monthly_income / 30.5) * self.days.days, 2)

    def get_actual_spending_percent(self, df, filt):
        actual_spending = self.get_actual_spending(df, filt)
        expected_income = self.get_expected_income(df, filt)
        percent = -actual_spending / expected_income
        #TODO returns a -0.0 for zeros sometimes? must solve
        return round(percent, 2)

    def get_expected_spending_percent(self, df, filt):
        if not self.has_budget:
            return "No Budget"
        else:
            percent = self.has_budget / 100
            return round(percent, 2)
    
    def get_expected_spending(self, df, filt):
        if not self.has_budget:
            return "No Budget"
        else:
            expected_percent = self.get_expected_spending_percent(df, filt)
            expected_income = self.get_expected_income(df, filt)
            spending = -expected_percent * expected_income
            return round(spending, 2)

    def get_over_budget(self, df, filt):
        if not self.has_budget:
            return "No Budget"
        else:
            amount_over = self.get_amount_over_expected(df, filt)
            return True if amount_over > 0 else False

    def get_amount_over_expected_percent(self, df, filt):
        if not self.has_budget:
            return "No Budget"
        else:
            actual_spending = self.get_actual_spending(df, filt)
            expected_spending = self.get_expected_spending(df, filt)
            percent = (expected_spending + (-actual_spending)) / -expected_spending
            return round(percent, 2)

    def get_amount_over_expected(self, df, filt):
        if not self.has_budget:
            return "No Budget"
        else:
            actual_spending = self.get_actual_spending(df, filt)
            expected_spending = self.get_expected_spending(df, filt)
            return round(expected_spending + (-actual_spending), 2)

    def point_to_df(self, display_data_type="actual_spending"):
        function = self.ANALYSIS_TYPES[display_data_type]
        dictionary = {
            "Row ID" : self.row_id,
            "Start Date" : [self.start_date],
            "End Date" : [self.end_date],
            self.category : [function(self.df, self.filt)]
        }
        return pd.DataFrame(dictionary)
    
    def __add__(self, data_frame):
        assert data_frame["Row ID"].iloc[0] == self.row_id
        assert data_frame["Start Date"].iloc[0] == self.start_date
        assert data_frame["End Date"].iloc[0] == self.end_date
        category_series = self.point_df[self.category]
        data_frame[self.category] = category_series
        return data_frame


class RowConstructor():
    def __init__(
        self, df, analysis_type, search_column, 
        category_list, date_range, 
        avg_monthly_income, budget=None,
    ):
        # set main class attributes
        self.categories = category_list
        self.date_range = date_range
        self.datetime_range = range_to_datetimes(date_range)
        self.data_frame = pd.DataFrame(
            {
                "Row ID" : [date_range],
                "Start Date" : [self.datetime_range["start"]],
                "End Date" : [self.datetime_range["end"]]
            }
        )

        self.gross_gain = 0
        self.gross_loss = 0
        self.data_point_objects = {}
        # loop through categories and add them to the dataframe as columns
        for category in self.categories:
            if budget != None and category != "Income":
                self.budget = budget
            else:
                self.budget = {category : None}
            column_item = DataPointConstructor(
                df, analysis_type, category, search_column,
                avg_monthly_income, date_range, 
                budget_percent=self.budget[category]
            )
            self.data_frame = column_item + self.data_frame
            self.data_point_objects[category] = column_item
            if column_item.actual_spending > 0:
                self.gross_gain += column_item.actual_spending
            elif column_item.actual_spending < 0:
                self.gross_loss += column_item.actual_spending

    def net_income_row(self, df_template):
        df_template["Row ID"] = self.date_range
        df_template["Start Date"] = self.datetime_range["start"]
        df_template["End Date"] = self.datetime_range["end"]
        df_template["Gross Income"] = self.gross_gain
        df_template["Gross Spending"] = self.gross_loss
        df_template["Net Income"] = self.gross_gain - self.gross_loss 
        print(df_template)
        return df_template  

    def income_row(self, df_template):
        pass

    def comparison_row(self, df_template, comparison_map):
        pass

    def __add__(self, data_frame):
        assert list(self.data_frame.columns) == list(data_frame.columns)
        return self.data_frame.append(data_frame)


class TableConstructor():
    def __init__(
        self, controller, df, analysis_type, search_column,
        date_range_list, category_list, 
        avg_monthly_income, budget=None, 
        comparison=False
    ):
        # define key attributes
        self.comparison_analysis_map = controller.config.COMPARISON_ANALYSIS_MAP
        self.df = df
        self.search_column = search_column
        self.avg_monthly_income = avg_monthly_income
        self.budget = budget
        self.analysis_type = analysis_type
        self.date_range_list = date_range_list
        self.categories = category_list

        # loop over date ranges and add rows together
        self.row_objects = {}
        self.data_frame = pd.DataFrame(
            columns=["Row ID", "Start Date", "End Date", *self.categories]
        )
        for date_range in self.date_range_list:
            row = RowConstructor(
                self.df, self.analysis_type, self.search_column,
                self.categories, date_range, 
                self.avg_monthly_income, self.budget
            )
            self.data_frame = row + self.data_frame
            self.row_objects[date_range] = row

        if comparison:
            self.comparison_analysis(self.comparison_analysis_map[self.analysis_type])

        self.data_frame.sort_values(by=["Start Date"], inplace=True)
        self.data_frame.set_index("Start Date")

    def comparison_analysis(self, analysis_map):
        df_constructor =  pd.DataFrame(columns=["Row ID", "Start Date", "End Date", *analysis_map["columns"]])
        self.data_frame = df_constructor.copy()
        for row in self.row_objects:
            if analysis_map["table keys"] == "net":
                new_row = self.row_objects[row].net_income_row(df_constructor)
            elif analysis_map["table keys"] == "income":
                new_row = self.row_objects[row].income_row(df_constructor)
            else:
                new_row = self.row_objects[row].comparison_row(df_constructor, analysis_map)
            # self.data_frame = self.data_frame.append(new_row)