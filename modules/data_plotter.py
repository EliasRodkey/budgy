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
            "Line Chart" : self.build_line_plot, 
            "Table": self.build_table, 
            "Bar Graph" : self.build_bar_graph,
            "Comparison Chart" : self.build_comparison_chart,
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
        explode = self.find_explosion(x)
        self.plot.pie(
            x, explode=tuple(explode),
            radius=1.1, autopct='%1.2f%%',
            pctdistance=0.8, colors=colors,
            textprops={"fontsize" : 14}
        )
        self.plot.legend(labels)
    
    def clean_pie_data(self):
        # removes income information to avoid confussion with negatives
        labels = self.columns.copy()
        if "Income" in labels:
            labels.remove("Income")
        # list of values for pie chart
        x = self.df[labels].iloc[0].tolist()
        # removes any categories with a value of 0
        print(x)
        remove = []
        for i, column in enumerate(labels):
            if x[i] < 0:
                x[i] = -x[i]
            if round(x[i], 2) <= 0.0:
                remove.insert(0, (i, column))
        for item in remove:
            del x[item[0]]
            labels.remove(item[1])
        # absolute value loop
        for i, num in enumerate(x):
            x[i] = abs(num)
        return x, labels
    
    @staticmethod
    def find_explosion(x):
        explode = []
        for i in x:
            temp = 30 / i
            if temp > 0.5:
                temp = 0.5
            explode.append(temp)
        return explode

    def build_line_plot(self):
        colors = self.generate_colors(len(self.columns))
        for i, name in enumerate(self.columns):
            self.plot.plot(
                self.df["Start Date"].astype("str"), 
                self.df[name], color=colors[i], marker="x"
            )
        self.plot.xlabel("Date", fontdict={"fontsize" : 16})
        self.plot.ylabel("Dollars", fontdict={"fontsize" : 16})
        self.plot.axhline(0, color="black")
        self.plot.legend(self.columns)

    def build_table(self):
        ax = self.plot.subplot(111, frame_on=False) 
        ax.xaxis.set_visible(False) 
        ax.yaxis.set_visible(False)
        
        table_vals, col_labels = self.clean_table_data()
        the_table = self.plot.table(
            cellText=table_vals,
            #colWidths = [0.5]*len(col_labels),
            #rowLabels=row_labels, 
            colLabels=col_labels, loc="center",
            cellLoc="center", rowLoc = "center"
        )
        the_table.auto_set_font_size(False)
        the_table.set_fontsize(14)
        the_table.scale(1.2, 2)

    def clean_table_data(self):
        display_table = self.df[["Start Date", *self.columns]]
        display_table["Start Date"] = display_table["Start Date"].astype("str")
        vals = display_table.values
        col_labels = display_table.columns.tolist()
        # row_labels = display_table["Row ID"]
        return vals, col_labels
        
    def build_bar_graph(self):
        labels, bottom = self.clean_bar_data()
        colors = self.generate_colors(len(labels))
        for i, name in enumerate(labels):
            self.plot.bar(
                self.df["Start Date"].astype("str"),
                self.df[name], label=name,
                color=colors[i], bottom=bottom["Bottom"],
            )
            new_bottom = bottom["Bottom"].add(self.df[name], fill_value=0)
            bottom["Bottom"] = new_bottom
        self.plot.xlabel("Date", fontdict={"fontsize" : 16})
        self.plot.ylabel("Dollars", fontdict={"fontsize" : 16})
        self.plot.axhline(0, color="black")
        self.plot.legend()

    def clean_bar_data(self):
        labels = self.columns.copy()
        if "Income" in labels:
            labels.remove("Income")
        rows = self.df.shape[0]
        temp = [0 for i in range(rows)]
        dictionary = {
            "Start Date" : self.df["Start Date"],
            "Bottom" : temp
        }
        bottom = pd.DataFrame(dictionary)
        bottom.set_index("Start Date")
        return labels, bottom
    
    def build_comparison_chart(self):
        colors = ["g", "r"]
        for i in range(2):
            self.plot.plot(
                self.df["Start Date"].astype("str"),
                self.df.iloc[:, i+3], color=colors[i],
                marker="x", label=self.columns[i]
            )
        
        gmask = self.df[self.columns[2]] >= 0 
        rmask = self.df[self.columns[2]] < 0

        self.plot.bar(
            self.df[gmask]["Start Date"].astype("str"),
            self.df[gmask][self.columns[2]],
            color="g", label=self.columns[-1]
        )
        self.plot.bar(
            self.df[rmask]["Start Date"].astype("str"),
            self.df[rmask][self.columns[2]],
            color="r", label=self.columns[-1]
        )
        self.plot.legend()

    def generate_colors(self, num_of_plots):
        colors_256 = sample(self.COLOR_LIST, num_of_plots)
        colors = []
        for color in colors_256:
            temp = []
            for rgb in color:
                temp.append(rgb / 256)
            colors.append(tuple(temp))
        return colors
    
    def show(self):
        self.plot.show()
    
    def save(self):
        pass