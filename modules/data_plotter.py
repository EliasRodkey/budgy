#! python3
# data_plotter.py - reads data from csv_parser.py and plots
# a variety of graphs for data visulization
import pandas as pd
from random import sample
from matplotlib import pyplot as plt


class DataPlotter():
    # TODO: make parrallel graph comparing to budget
    def __init__(self, df, chart_type, breakdown, search_column):
        CHART_MAP = {
            "Pie Chart" : self.build_pie_chart,
            "Line Chart" : self.build_line_chart, 
            "Table": self.build_table, 
            "Bar Graph" : self.build_bar_graph, 
            "Histogram" : self.build_histogram
        }
        self.COLOR_LIST = [
            (178, 33, 179),
            (140, 104, 170),
            (224, 79, 127),
            (242, 228, 116),
            (101, 199, 44),
            (241, 144, 69),
            (20, 176, 185),
            (179, 26, 126),
            (103, 148, 225),
            (191, 60, 46),
            (41, 124, 59),
            (161, 78, 104),
            (74, 117, 242),
            (66, 74, 142),
            (254, 69, 6),
            (54, 206, 219)
        ]
        if search_column == "Category":
            title_category = "Subcategories"
        else:
            title_category = "General Categories"
        self.title = f"{chart_type} of {title_category}\nBreakdown: {breakdown}"
        self.df = df
        self.columns = self.df.columns.tolist()[3:]
        self.dates_df = self.df["Start Date"].dt.strftime("%m/%d/%Y")
        
        self.plot = plt
        self.plot.style.use("ggplot")
        self.plot.figure(figsize=(20, 15))
        function = CHART_MAP[chart_type]
        function()
    
    def build_pie_chart(self):
        x, labels = self.clean_pie_data()
        colors = self.generate_colors(len(x))
        explode = [(30/i) for i in x]
        self.plot.pie(
            x, explode=tuple(explode),
            radius=1.1, autopct='%1.2f%%',
            pctdistance=0.8, colors=colors,
            textprops={"fontsize" : 14}
        )
        self.plot.legend(labels)
    
    def clean_pie_data(self):
        labels = self.columns.copy()
        if "Income" in labels:
            labels.remove("Income")

        x = self.df[labels].iloc[0].tolist()
        if self.title.split(" ")[-1] != "All":
            totals = []
            for column in labels:
                totals += self.df[column].sum()
            x = totals
        remove = []

        for i, column in enumerate(labels):
            if round(x[i], 1) == 0.0:
                remove.insert(0, (i, column))
        for item in remove:
            del x[item[0]]
            labels.remove(item[1])

        for i, num in enumerate(x):
            if num < 0:
                x[i] = -num
        return x, labels
    
    def generate_colors(self, num_of_plots):
        colors_256 = sample(self.COLOR_LIST, num_of_plots)
        colors = []
        for color in colors_256:
            temp = []
            for rgb in color:
                temp.append(rgb / 256)
            colors.append(tuple(temp))
        return colors


    def build_line_chart(self):
        pass

    def build_table(self):
        pass

    def build_bar_graph(self):
        pass

    def build_histogram(self):
        pass
    
    def show(self):
        self.plot.show()
    
    def save(self):
        pass


class DataPlotter2():
    def __init__(self, df):
        self.df = df
        self.ALL_CATEGORIES = category_breakdown
        self.time_span = time_span
        if self.time_span == None:
            self.time_span_text = ""
        else:
            self.time_span_text = f"{self.time_span}ly "

        self.sub_category = sub_category
        if self.sub_category == None:
            self.category_keys = list(self.ALL_CATEGORIES.keys())
        else:
            self.category_keys = self.ALL_CATEGORIES[self.sub_category]

        modified_dates = {"Dates" : []}
        for date in self.df["Date Ranges"]:
            date_list = date.split(" - ")
            modified_dates["Dates"].append(date_list[0])
        self.dates_df = pd.DataFrame(modified_dates)
    
    # plots total income, total loss, and net income loss for a given time span
    def net_income_plot(self):
        line_plot = plt
        line_plot.figure(figsize=(10, 8))
        columns = [("Gross Income", "green"), ("Gross Spending", "red"), ("Net Income/Loss", "blue")]
        for column, color in columns:
            line_plot.plot(self.dates_df["Dates"], self.df[column], f"{color[0]}.-", label=column)

        min_date = self.df.iloc[0]["Date Ranges"].split(" - ")[0]
        max_date = self.df.iloc[-1]["Date Ranges"].split(" - ")[1]
        line_plot.title(
            f"{self.time_span_text}Net Income \nfrom {min_date} to {max_date}", 
            fontdict={"fontsize": 20}
            )
        if self.time_span == "Month":
            line_plot.xticks(self.dates_df["Dates"][::6])
        elif self.time_span == "Year":
            line_plot.xticks(self.dates_df["Dates"])
        elif self.time_span == "Week":
            line_plot.xticks(self.dates_df["Dates"][::26])
        line_plot.xlabel("Date", fontdict={"fontsize" : 16})
        line_plot.ylabel("Dollars", fontdict={"fontsize" : 16})
        line_plot.axhline(0, color="black")
        line_plot.legend()
        line_plot.show()
        return line_plot

    # plots a single spending or budget category nicely formatted
    def plot_category(self, category="Net Income/Loss"):
        line_plot = plt
        line_plot.figure(figsize=(10, 8))
        line_plot.style.use("ggplot")
        line_plot.plot(self.dates_df["Dates"], self.df[category], ".-", label=category)

        min_date = self.df.iloc[0]["Date Ranges"].split(" - ")[0]
        max_date = self.df.iloc[-1]["Date Ranges"].split(" - ")[1]
        line_plot.title(
            f"{self.time_span_text}{category} Spending\nfrom {min_date} to {max_date}", 
            fontdict={"fontsize": 20}
            )
        if self.time_span == "Month":
            line_plot.xticks(self.dates_df["Dates"][::6])
        elif self.time_span == "Year":
            line_plot.xticks(self.dates_df["Dates"])
        elif self.time_span == "Week":
            line_plot.xticks(self.dates_df["Dates"][::26])
        line_plot.xlabel("Date", fontdict={"fontsize" : 16})
        line_plot.ylabel("Dollars", fontdict={"fontsize" : 16})
        line_plot.axhline(0, color="black")
        line_plot.legend()
        line_plot.show()
        return line_plot

    def plot_all_categories(self):
        line_plot = plt
        line_plot.figure(figsize=(12, 8))
        line_plot.style.use("ggplot")
        line_types = [".-", "--", "-"]
        line_count = 0
        for i, category in enumerate(self.df[self.category_keys]):
            line_plot.plot(self.dates_df["Dates"], self.df[category], line_types[line_count], label=category)
            print(line_count)
            if line_count == 2:
                line_count = 0
            else:
                line_count += 1

        min_date = self.df.iloc[0]["Date Ranges"].split(" - ")[0]
        max_date = self.df.iloc[-1]["Date Ranges"].split(" - ")[1]
        line_plot.title(
            f"{self.time_span_text}Spending Breakdown\nfrom {min_date} to {max_date}", 
            fontdict={"fontsize": 20}
            )
        if self.time_span == "Month":
            line_plot.xticks(self.dates_df["Dates"][::6])
        elif self.time_span == "Year":
            line_plot.xticks(self.dates_df["Dates"])
        elif self.time_span == "Week":
            line_plot.xticks(self.dates_df["Dates"][::26])
        line_plot.xlabel("Date", fontdict={"fontsize" : 16})
        line_plot.ylabel("Dollars", fontdict={"fontsize" : 16})
        line_plot.axhline(0, color="black")
        line_plot.legend(loc='lower left')
        line_plot.show()
        return line_plot

    def single_range_pie_chart(self):
        pie_chart = plt
        pie_chart.style.use("ggplot")
        pie_chart.figure(figsize=(12, 8))
        x, labels = self.find_correct_pie_columns()
        explode = [0.1 for i in labels]
        pie_chart.pie(
            x.abs(),
            explode=tuple(explode), 
            radius=1.1,
            autopct='%1.2f%%',
            pctdistance=0.8
        )
        dates = self.df["Date Ranges"].iloc[0].split(" - ")
        pie_chart.title(f"Spending Breadown\nfrom {dates[0]} to {dates[-1]}")
        pie_chart.legend(labels)
        pie_chart.show()

    def find_correct_pie_columns(self):
        if self.sub_category == None:
            x = self.df[self.category_keys].iloc[0].drop("Income")
            labels = self.category_keys[1:]
        else:
            x = self.df[self.category_keys].iloc[0]
            labels = self.category_keys
        remove = []
        for i, name in enumerate(labels):
            if self.df[name].iloc[0] == 0:
                remove.append((i, name))
        for i, name in remove:
            labels.remove(name)
            x = x.drop(name)
        return x, labels