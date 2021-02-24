#! python3
# model.py - houses all model classes and passes information from
# the controller ot the model

from modules import csv_parser
from modules import data_plotter
from modules import date_finder

class Model():
    def __init__(self, controller, local_path, category_breakdown):
        self.csv_data = csv_parser.CSVAnalyzer(local_path, category_breakdown)
        self.df = self.csv_data.df
        self.date_ranges = date_finder.DateFinder
        self.table_maker = csv_parser.TableConstructor
        self.plotter = data_plotter.DataPlotter
        self.all_time_transaction_dates = self.find_first_last_transaction()
    
    def find_first_last_transaction(self):
        self.start = self.df["Date"].min().to_pydatetime()
        self.end = self.df["Date"].max().to_pydatetime()
        return f"{self.start.strftime('%m/%d/%Y')} - {self.end.strftime('%m/%d/%Y')}"