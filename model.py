#! python3
# model.py - houses all model classes and passes information from
# the controller ot the model

from modules import csv_parser, data_plotter

class Model():
    def __init__(self, controller, local_path, category_breakdown):
        self.csv_data = csv_parser.CSVAnalyzer(local_path, category_breakdown)
        self.plotter = data_plotter.DataPlotter