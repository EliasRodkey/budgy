import os

class Config():
    def __init__(self):
        # contains path to local transactions file
        self.LOC_TRANSACTION_PATH = os.path.join(os.getcwd(), "transactions.csv")
        self.LOC_SHELF_PATH = os.path.join("shelf", "shelf")
        self.CHART_TYPES = ["Pie Chart", "Line Chart", "Table", "Bar Graph", "Histogram"]
        self.ANALYSIS_TYPES = {
            "Actual Spending ($)" : {
                "table key" : "actual_spending",
                "compatible graphs" : self.CHART_TYPES[:3]
            }, 
            "Actual Spending (%)" : {
                "table key" : "actual_spending_percent",
                "compatible graphs" : self.CHART_TYPES[:3]
            },
            "Transactions" : {
                "table key" : "transactions",
                "compatible graphs" : self.CHART_TYPES[2]
            }, 
            "Number Of Transactions" : {
                "table key" : "transaction_number",
                "compatible graphs" : self.CHART_TYPES
            },
            "Expected Income" : {
                "table key" : "expected_income",
                "compatible_graphs" : self.CHART_TYPES[:3]
            },
            "Budgeted Spending (%)" : {
                "table key" : "expected_spending_percent",
                "compatible graphs" : self.CHART_TYPES[:3]
            }, 
            "Budgeted Spending ($)" : {
                "table key" : "expected_spending",
                "compatible graphs" : self.CHART_TYPES[:3]
            }, 
            "Amount Over/Under Budget ($)" : {
                "table key" : "amount_over",
                "compatible graphs" : self.CHART_TYPES[:3]
            },
            "Amount Over/Under Budget (%)" : {
                "table key" : "amount_over_percent",
                "compatible graphs" : self.CHART_TYPES[:3]
            },
            "Over Budget (T/F)" : {
                "table key" : "over_budget",
                "compatible graphs" : self.CHART_TYPES[2:3]
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