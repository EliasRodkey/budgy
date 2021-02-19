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
import calendar
from random import randint


def range_to_datetimes(date_range):
    rang = date_range.split(" - ")
    old_date = datetime.datetime.strptime(rang[0], "%m/%d/%Y")
    new_date = datetime.datetime.strptime(rang[1], "%m/%d/%Y")
    return {"start" : old_date, "end" : new_date}

def datetimes_to_range(datetimes):
    old_date = datetimes["start"].strftime("%m/%d/%Y")
    new_date = datetimes["end"].strftime("%m/%d/%Y")
    return f"{old_date} - {new_date}"


class CSVAnalyzer():
    def __init__(self, local_path, category_breakdown):
        self.ALL_CATEGORIES = category_breakdown
        self.local_path = local_path
        self.df = pd.read_csv(self.local_path)
        self.clean_df()

        # makes sure controller works
        self.all_time_dates = self.find_all_time_date_range()
        self.all_time_dates_str = self.all_time_dates["Date Ranges"].iloc[0]

    # returns the date of the first transactions and the date of the last transaction
    def find_all_time_date_range(self):
        oldest = self.df["Date"].min()
        newest = self.df["Date"].max()
        string = f"{oldest.strftime('%m/%d/%Y')} - {newest.strftime('%m/%d/%Y')}"
        return pd.DataFrame([string], columns=["Date Ranges"])
        
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
        category, 
        search_column, 
        budget_percent, 
        avg_monthly_income, 
        date_range
    ):
        self.df = df
        self.category = category
        self.subcategory = True if search_column == "Category" else False
        self.date_range = range_to_datetimes(date_range)
        self.start_date = self.date_range["start"]
        self.end_date = self.date_range["end"]
        days = self.end_date - self.start_date
        # filters whoel df for transactions between the start and end dates in the 
        # correct category
        filt = (self.df["Date"] >= self.start_date) \
            & (self.df["Date"] <= self.end_date) \
            & (self.df[search_column] == category)
        self.transactions = self.df[filt]
        self.amount = self.transactions["Amount"].sum()
        # budget assessment attributes
        self.expected_income = days.days / 30.5 * avg_monthly_income
        self.expected_spending_percent = budget_percent / 100
        self.expected_spending = self.expected_income * -self.expected_spending_percent
        self.over_budget = True if -self.amount > self.expected_spending else False
        self.actual_spending_percent = -self.amount / self.expected_income


class RowConstructor():
    def __init__(self, date_range, subcategory=None):
        self.subcategory = subcategory
        self.datetime_range = self.range_to_datetimes(date_range)
        self.category_data_point("Shopping")
    
    def date_range_row(self):
        pass
        

if __name__ == "__main__":
    import os
    LOC_TRANSACTION_PATH = os.path.join(os.getcwd(), "transactions.csv")
    LOC_SHELF_PATH = os.path.join("shelf", "shelf")
    AVG_MONTHLY_INCOME = 1740
    # TODO: tie budget to UI
    EXAMPLE_BUDGET = {
        'save_date': '02/18/2021', 
        'Bills/Utilities': 75, 
        'Food': 15, 
        'Drink': 5, 
        'Car': 2, 
        'Shopping': 3, 
        'Entertainment': 2, 
        'Travel': 3, 
        'Health': 1, 
        'Education': 1, 
        'Investments': 10, 
        'Business': 1, 
        'Taxes': 1, 
        'Other': 1
    }
    ALL_CATEGORIES = {  #contains all possible categories from mint.com transactions
                "Income" : [
                    "Income", "Bonus", "Interest Income", "Paycheck", "Reimbursment", 
                    "Rental Income", "Returned Purchase", "Check",
                    ],
                "Bills/Utilities" : [
                    "Bills & Utilities", "Home Phone", "Internet", "Mobile Phone", "Television", 
                    "Utilities", "Mortgage & Rent", "Loan Payment", "Subscription", "Venmo Charge"
                    ],
                "Food" : [
                    "Fast Food", "Groceries", "Restaurants", "Food & Dining"],
                "Drink" : [
                    "Alcohol & Bars", "Coffee Shops"
                    ],
                "Car" : [
                    "Auto Insurance", "Auto Payment", "Parking", "Public Transportation"
                    ],
                "Shopping" : [
                    "Shopping", "Books", "Clothing", "Electronics & Software", "Hobbies", 
                    "Sporting Goods", "Amazon Purchases"
                    ],
                "Entertainment" : [
                    "Amusement", "Arts", "Movies & DVDs", "Music", "Newspapers & Magazines",
                    "Video Games", "Concerts"
                    ],
                "Travel" : [
                    "Travel", "Air Travel", "Hotel", "Rental Car & Taxi", "Vacation"
                    ],
                "Health" : [
                    "Health & Fitness", "Dentist", "Doctor", "Eyecare", "Gym", 
                    "Health Insurance", "Pharmacy", "Sports"
                    ],
                "Education": [
                    "Books & Supplies", "Studeny Loan", "Tuition"
                    ],
                "Investments" : [
                    "Trade Commissions", "Finance Charge", "Investments", "Buy", "Deposit", 
                    "Dividend & Cap Gains", "Sell", "Withdrawal"
                    ],
                "Business" : [
                    "Advertising", "Business Services"
                    ],
                "Taxes" : [
                    "Taxes", "Federal Tax", "Local Tax", "Property Tax", "Sales Tax", "State Tax"],
                "Other"	 : [
                    "Business Services", "Office Supplies", "Fees & Charges", "ATM Fee",    
                    "Late Fee", "Service Fee", "Gifts & Donations", "Furnishings", 
                    "Home Improvement", "Loans", "Hair", "Transfer for Cash Spending",
                    "Uncategorized", "Cash & ATM", "Transfer", "Printing", "Shipping"
                    # "Credit Card Payment", "Laundry", "Spa & Massage", "Loan Fees and Charges", 
                    # "Loan Principal", "Personal Care", "Loan Insurance", "Loan Interest",
                    # "Kids", "Allowance", "Baby Supplies", "Babysitter & Daycare", "Child Support",
                    # "Kids Activities", "Pets", "Pet Food & Supplies", "Pet Grooming", "Veterinary",
                    # "Home Insurance", "Home Services", "Financial Advisor", "Life Insurance",
                    # "Charity", "Gift", "Bank Fee", "Misc Expenses", "Financial", "Home",
                    # "Lawn & Garden", "Toys", "Home Supplies", "Legal",
                    ]
            }
    
    import pprint
    analyze = CSVAnalyzer(LOC_TRANSACTION_PATH, ALL_CATEGORIES)
    old = "1/7/2019"
    new = "1/1/2021"
    # analyze.update_csv_file()
    point = DataPointConstructor(
        analyze.df, "Food", "General Category", 
        EXAMPLE_BUDGET["Food"], AVG_MONTHLY_INCOME, f"{old} - {new}"
    )
    print(point.actual_spending_percent)
    print(point.amount)




class CSVAnalyzer2():
    def __init__(self, local_path, category_breakdown):
        # create lists of weeks and a list of months and years to filter by later
        self.all_time_dates = self.find_all_time_date_range()
        self.all_time_dates_str = self.all_time_dates["Date Ranges"].iloc[0]
        self.years = self.find_years(self.all_time_dates_str)
        self.months = self.find_months(self.all_time_dates_str)
        self.weeks = self.find_weeks()

    # provides a pandas dataframe with a breakdown of spending / income 
    # by categpory in a given time frame including a total income, total spending, 
    # and net gain/loss column
    def spending_breakdown(self, date_range_df, sub_category=None): 
        self.categories = {}
        self.categories["Net Income/Loss"] = []
        self.categories["Gross Income"] = []
        self.categories["Gross Spending"] = []
        if sub_category == None:
            cat_column = "General Category"
            for category in self.ALL_CATEGORIES.keys():
                self.categories[category] = []
        else:
            cat_column = "Category"
            for category in self.ALL_CATEGORIES[sub_category]:
                self.categories[category] = []

        for i, series in date_range_df.iterrows():
            rng = series[0].split(" - ")
            low_date = datetime.datetime.strptime(rng[0], "%m/%d/%Y")
            high_date = datetime.datetime.strptime(rng[1], "%m/%d/%Y")
            income_subtotal = 0
            spending_subtotal = 0
            for category in list(self.categories.keys())[3:]:
                filt = (self.df["Date"] >= low_date) \
                    & (self.df["Date"] <= high_date) \
                    & (self.df[cat_column] == category);
                column_sum = self.df[filt]["Amount"].sum()
                if column_sum > 0:
                    income_subtotal += column_sum
                elif column_sum < 0:
                    spending_subtotal += column_sum
                else:
                    self.categories[category].append(0)
                if column_sum != 0:
                    self.categories[category].append(column_sum)
            self.categories["Gross Income"].append(income_subtotal)
            self.categories["Gross Spending"].append(spending_subtotal)
            self.categories["Net Income/Loss"].append((income_subtotal + spending_subtotal))

        spending_df = pd.concat(
            [
                date_range_df, 
                pd.DataFrame(self.categories)
            ], 
            axis=1
            )
        return spending_df.round(2)

    # very similar to the spending breakdown but adds an income
    # columns and divides all categories by the total to get a percentage
    # of income in a given period
    def budget_breakdown(self, date_range_df, sub_category=None, divide_by_income=False):
        spending_breakdown_df = self.spending_breakdown(date_range_df, sub_category=sub_category)
        percentages = pd.DataFrame()
        percentages["Date Ranges"] = date_range_df["Date Ranges"]

        if divide_by_income:
            net_column = "Gross Income"
        else:
            net_column = "Gross Spending"
        for series in spending_breakdown_df:
            if series != None and series != "Date Ranges":
                try:
                    percentages[series] = spending_breakdown_df[series].div(abs(spending_breakdown_df[net_column]))
                except ZeroDivisionError:
                    logging.error(
                        f"Zero Division Error: couldn't divide: {spending_breakdown_df[series]}  by {spending_breakdown_df[net_column]}"
                    )
        return percentages #.rename(columns={"total"}) # return table dates, categories as a percentage of income or categories as a percentage of spending

    # similar to find_all_time_date range as it only returns a single set of dates
    # however the range can be customized
    def custom_date_range(self, old_date:str, new_date=datetime.datetime.now().strftime("%m/%d/%Y")):
        self.custom_dates_str = f"{old_date} - {new_date}"
        self.custom_dates = pd.DataFrame([self.custom_dates_str], columns=["Date Ranges"])
        self.years = self.find_years(self.custom_dates_str)
        self.months = self.find_months(self.custom_dates_str)
        self.weeks = self.find_weeks()

   

    # returns the start and end dates of each year in the transactions history
    def find_years(self, date_range):
        dates = date_range.split(" - ")
        oldest = datetime.datetime.strptime(dates[0], "%m/%d/%Y")
        newest = datetime.datetime.strptime(dates[1], "%m/%d/%Y")
        years_passed = newest.year - oldest.year
        years = []
        for i in range(years_passed + 1):
            current = oldest.year + i
            years.append(f"01/01/{current} - 12/31/{current}")
        years = self.sort_dates(years)
        return pd.DataFrame(years, columns=["Date Ranges"])

    # finds all of the months with transactions returned in a list of tuples
    def find_months(self, date_range):
        dates = date_range.split(" - ")
        oldest = datetime.datetime.strptime(dates[0], "%m/%d/%Y")
        newest = datetime.datetime.strptime(dates[1], "%m/%d/%Y")
        all_time_oldest = datetime.datetime.strptime(self.all_time_dates_str.split(" - ")[0], "%m/%d/%Y")
        all_time_newest = datetime.datetime.strptime(self.all_time_dates_str.split(" - ")[1], "%m/%d/%Y")
        if oldest < all_time_oldest:
            oldest = all_time_oldest
        if newest > all_time_newest:
            newest = all_time_newest
        months = []
        current = oldest
        while current <= newest:
            last_day = calendar.monthrange(current.year, current.month)[1]
            range_string = f"{current.strftime('%m/01/%Y')} - {current.strftime(f'%m/{last_day}/%Y')}"
            if range_string not in months:
                months.append(range_string)
            current += datetime.timedelta(days=6)
        months = self.sort_dates(months)
        return pd.DataFrame(months, columns=["Date Ranges"])
    
    # finds all the weeks (7 day periods) from first transaction until the beginning of transaciton hsitory
    def find_weeks(self):
        weeks = []
        for i, month in self.months.iterrows():
            month = month["Date Ranges"].split(" - ")[0]
            month_num = datetime.datetime.strptime(month, "%m/%d/%Y")
            raw_weeks = calendar.Calendar().monthdatescalendar(
                month_num.year, month_num.month
                )
            for week in raw_weeks:
                if f"{week[0].strftime('%m/%d/%Y')} - {week[-1].strftime('%m/%d/%Y')}" not in weeks:
                    weeks.append(f"{week[0].strftime('%m/%d/%Y')} - {week[-1].strftime('%m/%d/%Y')}")
        weeks = self.sort_dates(weeks)
        return pd.DataFrame(weeks, columns=["Date Ranges"])

    # sorts a range of dates from newest to oldest using quciksort method
    def sort_dates(self, array):
        if len(array) < 2:
            return array

        low, same, high = [], [], []

        rand_item = array[randint(0, len(array) - 1)]
        pivot = datetime.datetime.strptime(rand_item.split(" - ")[0], "%m/%d/%Y")

        for item in array:
            date = datetime.datetime.strptime(item.split(' - ')[0], "%m/%d/%Y")
            if date < pivot:
                low.append(item)
            elif date == pivot:
                same.append(item)
            elif date > pivot:
                high.append(item)
        return self.sort_dates(low) + same + self.sort_dates(high)