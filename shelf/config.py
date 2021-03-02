import os

class Config():
    def __init__(self):
        # contains path to local transactions file
        self.LOC_TRANSACTION_PATH = os.path.join(os.getcwd(), "transactions.csv")
        self.LOC_SHELF_PATH = os.path.join("shelf", "shelf")
        self.BREAKDOWNS = ["All", "Years", "Months", "Weeks"]
        self.CHART_BREAKDOWN_MAP = {
            "Pie Chart" :  [self.BREAKDOWNS[0]], 
            "Line Chart" : self.BREAKDOWNS[1:],
            "Table" : self.BREAKDOWNS[:3],
            "Bar Graph" : self.BREAKDOWNS[:3],
            "Comparison Chart" : self.BREAKDOWNS
        }
        self.CHART_TYPES = list(self.CHART_BREAKDOWN_MAP.keys())
        self.ANALYSIS_CHART_MAP = {
            "Net Income" : [self.CHART_TYPES[-1]],
            "Budget Side by Side ($)" : [self.CHART_TYPES[-1]],
            "Budget Side by Side (%)" : [self.CHART_TYPES[-1]],
            "Actual Spending ($)" : self.CHART_TYPES,
            "Actual Spending (%)" : self.CHART_TYPES,
            "Amount Over/Under Budget ($)" : self.CHART_TYPES[1:3],
            "Amount Over/Under Budget (%)" : self.CHART_TYPES[1:3],
            "Number Of Transactions" : self.CHART_TYPES,
            "Income Side by Side" : [self.CHART_TYPES[-1]],
            "Expected Income" : self.CHART_TYPES[1:3],
            "Budgeted Spending (%)" : self.CHART_TYPES[:3],
            "Budgeted Spending ($)" : self.CHART_TYPES[:3],
            "Over Budget (T/F)" : self.CHART_TYPES[2:4]
            # "Transactions" :  [self.CHART_TYPES[2]]
        }
        self.COMPARISON_ANALYSIS_MAP = {
            "net_income" : {
                "columns" : ["Gross Income", "Gross Spending", "Net Income"],
                "table keys" : "net", 
            },
            "budget_comparison" : {
                "columns" : ["Expected Spending", "Actual Spending", "Amount Over/Under Budget"],
                "table keys" : ("actual_spending", "expected_spending"), 
            },
            "budget_comparison_percent" : {
                "columns" : ["Expected Spending", "Actual Spending", "Amount Over/Under Budget"],
                "table keys" : ("actual_spending_percent", "expected_spending_percent"),
            },
            "income_comparison" : {
                "columns" : ["Expected Income", "Actual Income", "Amount Over/Under Budget"],
                "table keys" : "income"
            }
        }
        self.ALL_CATEGORIES = {  #contains all possible categories from mint.com transactions
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