#! python3
# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'view.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# view.py - houses definitions for ui elements associated with 
# the budget analysis (budgy) application 

from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import datetime

# View() creates the qt application and is passed to the controller
# it also contains references to the other widgets so only
# View() needs to be imported
class View(QtWidgets.QMainWindow):
    def __init__(self, controller):
        self.controller = controller
        self.app = QtWidgets.QApplication(sys.argv)
        super().__init__()

        self.title_page = TitlePage(self.controller)
        self.spending_analysis_page = SpendingAnalysisPage(self.controller)
        self.budget_edit_page = BudgetEditPage(self.controller)

    # causes the built ui to show up for the user
    def show_ui(self):
        self.show()
        sys.exit(self.app.exec_())

    # sets up the layout and widgets of the ui using data from the
    # controller and model
    def setup_ui(self):
        self.setObjectName("Budgy")
        self.resize(1600, 1000)
        self.setWindowTitle("Budgy")

        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget.setStatusTip("Budgy")

        self.stackedWidget = QtWidgets.QStackedWidget(self.centralwidget)
        self.stackedWidget.setGeometry(QtCore.QRect(0, 0, 1600, 1500))
        self.stackedWidget.setObjectName("stackedWidget")
        self.stackedWidget.setStatusTip("Budgy")

        self.stackedWidget.addWidget(self.title_page)
        self.stackedWidget.addWidget(self.spending_analysis_page)
        self.stackedWidget.addWidget(self.budget_edit_page)

        self.setCentralWidget(self.centralwidget)

        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")

        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")

        self.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")

        self.setStatusBar(self.statusbar)

        self.actionEdit_Budget = QtWidgets.QAction(self)
        self.actionEdit_Budget.setObjectName("actionEdit_Budget")
        self.actionEdit_Budget.setText("Edit Budget")
        self.actionEdit_Budget.triggered.connect(
            lambda : self.controller.show_page(self.controller.view.budget_edit_page)
        )
        self.actionEdit_Budget.setShortcut("Ctrl+E")

        self.actionGenerate_summary = QtWidgets.QAction(self)
        self.actionGenerate_summary.setObjectName("actionGenerate_summary")
        self.actionGenerate_summary.setText("Generate Summary")
        self.actionGenerate_summary.setShortcut("Ctrl+S")
        self.actionGenerate_summary.setStatusTip("Generate Summary .PDF file")

        self.actionUpdate_Transactions = QtWidgets.QAction(self)
        self.actionUpdate_Transactions.setObjectName("actionUpdate_Transactions")
        self.actionUpdate_Transactions.setText("Update_Transactions")
        self.actionUpdate_Transactions.setShortcut("Ctrl+U")
        self.actionUpdate_Transactions.setStatusTip("Update Transactions CSV from Mint")

        self.actionExit = QtWidgets.QAction(self)
        self.actionExit.setObjectName("actionExit")
        self.actionExit.setText("Exit")
        self.actionExit.setShortcut("Esc")

        self.menuFile.addAction(self.actionUpdate_Transactions)
        self.menuFile.addAction(self.actionEdit_Budget)
        self.menuFile.addAction(self.actionGenerate_summary)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuFile.setTitle("File")

        self.menubar.addAction(self.menuFile.menuAction())

        self.stackedWidget.setCurrentWidget(self.title_page)
        self.controller.page_history.append(self.title_page)
        QtCore.QMetaObject.connectSlotsByName(self)


class TitlePage(QtWidgets.QWidget):
    def __init__(self, controller):
        self.controller = controller
        super().__init__()
        self.page_setup()

    def page_setup(self):
        self.setObjectName("Title Page")

        self.title = QtWidgets.QLabel(self)
        self.title.setGeometry(QtCore.QRect(0, 100, 1600, 150))
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        self.title.setText("Budgy")
        self.title.setStatusTip("Budgy")

        self.description = QtWidgets.QLabel(self)
        self.description.setGeometry(QtCore.QRect(500, 300, 600, 250))
        self.description.setText("ADD DESCRIPTION")
        self.description.setAlignment(QtCore.Qt.AlignCenter)
        self.description.setStatusTip("Budgy Description")

        self.next_button = QtWidgets.QPushButton(self)
        self.next_button.setGeometry(QtCore.QRect(700, 600, 200, 50))
        self.next_button.setText("Continue...")
        self.next_button.setStatusTip("Continue to Analysis")
        self.next_button.clicked.connect(
            lambda : self.controller.show_page(self.controller.view.spending_analysis_page)
        )
        self.next_button.setShortcut("Return")


class SpendingAnalysisPage(QtWidgets.QWidget):
    def __init__(self, controller):
        self.controller = controller
        super().__init__()

        # subclass
        class CheckableComboBox(QtWidgets.QComboBox):
            # once there is a checkState set, it is rendered
            # here we assume default Unchecked
            def addItem(self, item):
                super(CheckableComboBox, self).addItem(item)
                item = self.model().item(self.count()-1,0)
                item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                item.setCheckState(QtCore.Qt.Unchecked)

            def itemChecked(self, index):
                item = self.model().item(index,0)
                return item.checkState() == QtCore.Qt.Checked

        self.page_setup()

    def page_setup(self):
        self.setObjectName("Spending Analysis Page")
        self.setStatusTip("Spending Analyzer")

        self.title = QtWidgets.QLabel(self)
        self.title.setGeometry(QtCore.QRect(0, 0, 1600, 150))
        self.title.setText("Spending Analyzer")
        self.title.setStatusTip("Spending Analysis Page")
        self.title.setAlignment(QtCore.Qt.AlignCenter)

        self.data_display_type_label = QtWidgets.QLabel(self)
        self.data_display_type_label.setGeometry(QtCore.QRect(350, 200, 300, 50))
        self.data_display_type_label.setObjectName("data_display_type_label")
        self.data_display_type_label.setText("Analysis Type")

        self.data_display_type_comboBox = QtWidgets.QComboBox(self)
        self.data_display_type_comboBox.setGeometry(QtCore.QRect(350, 250, 300, 50))
        self.data_display_type_comboBox.addItem("Select One...")
        self.data_display_type_comboBox.addItems(
            list(self.controller.config.ANALYSIS_TYPES.keys())
        )
        self.data_display_type_comboBox.setObjectName("data_display_type_comboBox")
        self.data_display_type_comboBox.setStatusTip("Choose Analysis Type")

        self.chart_type_label = QtWidgets.QLabel(self)
        self.chart_type_label.setGeometry(QtCore.QRect(350, 320, 300, 50))
        self.chart_type_label.setObjectName("chart_type_label")
        self.chart_type_label.setText("Chart Type")

        self.chart_type_comboBox = QtWidgets.QComboBox(self)
        self.chart_type_comboBox.setGeometry(QtCore.QRect(350, 370, 300, 50))
        self.chart_type_comboBox.setObjectName("chart_type_comboBox")
        self.chart_type_comboBox.addItem("Select One...")
        self.chart_type_comboBox.addItem("Line")
        self.chart_type_comboBox.addItem("Pie")
        self.chart_type_comboBox.setStatusTip("Choose Chart Type")

        self.time_period_label = QtWidgets.QLabel(self)
        self.time_period_label.setGeometry(QtCore.QRect(350, 440, 300, 50))
        self.time_period_label.setObjectName("time_period_label")
        self.time_period_label.setText("Breakdown")

        self.time_period_combobox = QtWidgets.QComboBox(self)
        self.time_period_combobox.setGeometry(QtCore.QRect(350, 490, 300, 50))
        self.time_period_combobox.setObjectName("time_period_combobox")
        self.time_period_combobox.addItem("Select One...")
        self.time_period_combobox.addItem("All")
        self.time_period_combobox.addItem("Years")
        self.time_period_combobox.addItem("Months")
        self.time_period_combobox.addItem("Weeks")
        self.time_period_combobox.setStatusTip("Choose Time Breakdown")

        self.sub_category_label = QtWidgets.QLabel(self)
        self.sub_category_label.setGeometry(QtCore.QRect(350, 560, 300, 50))
        self.sub_category_label.setObjectName("sub_category_label")
        self.sub_category_label.setText("Categories")

        self.sub_category_combobox = QtWidgets.QComboBox(self)
        self.sub_category_combobox.setGeometry(QtCore.QRect(350, 610, 300, 50))
        self.sub_category_combobox.setObjectName("sub_category_combobox")
        self.sub_category_combobox.addItem("Select Multiple...")
        self.sub_category_combobox.setStatusTip("Choose Category for Analysis")

        self.sub_category_checkbox = QtWidgets.QCheckBox(self)
        self.sub_category_checkbox.setGeometry(QtCore.QRect(350, 660, 30, 50))

        self.checkbox_label = QtWidgets.QLabel(self)
        self.checkbox_label.setGeometry(QtCore.QRect(380, 660, 270, 50))
        self.checkbox_label.setObjectName("checkbox_label")
        self.checkbox_label.setText("View Subcategories")

        # self.date_range_box = QtWidgets.QGroupBox(self)
        # self.date_range_box.setGeometry(QtCore.QRect(230, 500, 1100, 110))
        # self.date_range_box.setObjectName("date_range_box")
        # self.date_range_box.setTitle("Time Frame")
        # self.date_range_box.setStatusTip("Choose Date Range of Analysis")

        # retrieves all time spending date ranges from model
        date_range = self.controller.model.all_time_transaction_dates.split(" - ")
        old_date = date_range[0].split("/")
        new_date = date_range[1].split("/")
        start_date = QtCore.QDate(int(old_date[-1]), int(old_date[0]), int(old_date[1]))
        end_date = QtCore.QDate(int(new_date[-1]), int(new_date[0]), int(new_date[1]))

        # self.start_date = QtWidgets.QDateEdit(self.date_range_box)
        # self.start_date.setGeometry(QtCore.QRect(200, 40, 300, 50))
        # self.start_date.setDate(start_date)
        # self.start_date.setMinimumDate(start_date)
        # self.start_date.dateChanged.connect(
        #     self.set_min_date
        # )
        # self.start_date.setObjectName("start_date")
        # self.start_date.setStatusTip("Choose Start Date of Analysis")

        # self.end_date = QtWidgets.QDateEdit(self.date_range_box)
        # self.end_date.setGeometry(QtCore.QRect(750, 40, 300, 50))
        # self.end_date.setDate(end_date)
        # self.end_date.setMaximumDate(end_date)
        # self.end_date.dateChanged.connect(
        #     self.set_max_date
        # )
        # self.end_date.setObjectName("end_date")
        # self.end_date.setStatusTip("Choose End Date of Analysis")

        # self.from_label = QtWidgets.QLabel(self.date_range_box)
        # self.from_label.setGeometry(QtCore.QRect(50, 40, 100, 50))
        # self.from_label.setObjectName("from_label")
        # self.from_label.setText("From:")
        # self.from_label.setAlignment(QtCore.Qt.AlignCenter)
        # self.from_label.setStatusTip("Choose Start Date of Analysis")

        # self.to_label = QtWidgets.QLabel(self.date_range_box)
        # self.to_label.setGeometry(QtCore.QRect(600, 40, 100, 50))
        # self.to_label.setObjectName("to_label")
        # self.to_label.setText("To:")
        # self.to_label.setAlignment(QtCore.Qt.AlignCenter)
        # self.to_label.setStatusTip("Choose End Date of Analysis")

        # self.analyze_spending_button = QtWidgets.QPushButton(self)
        # self.analyze_spending_button.setGeometry(QtCore.QRect(250, 500, 500, 100))
        # self.analyze_spending_button.setText("ANALYZE\nSPENDING")
        # self.analyze_spending_button.setStatusTip("Analyze Spending of given period")

        # self.analyze_budget_button = QtWidgets.QPushButton(self)
        # self.analyze_budget_button.setGeometry(QtCore.QRect(850, 500, 500, 100))
        # self.analyze_budget_button.setText("ANALYZE\nBUDGET")
        # self.analyze_budget_button.setStatusTip("Analyze Spending of given period")

    def set_min_date(self, value):
        self.end_date.setMinimumDate(value)
    
    def set_max_date(self, value):
        self.start_date.setMaximumDate(value)


class BudgetEditPage(QtWidgets.QWidget):
    def __init__(self, controller):
        self.controller = controller
        super().__init__()
        self.page_setup()
    
    def page_setup(self):
        self.setObjectName("Budget Edit Page")
        self.setStatusTip("Budget Goal Editor")

        self.title = QtWidgets.QLabel(self)
        self.title.setGeometry(QtCore.QRect(0, 0, 1600, 150))
        self.title.setText("Budget Goal Setter")
        self.title.setStatusTip("Budget Editing Page")
        self.title.setAlignment(QtCore.Qt.AlignCenter)

        self.income_label = QtWidgets.QGroupBox(self)
        self.income_label.setGeometry(QtCore.QRect(300, 150, 400, 80))
        self.income_label.setTitle("Average Monthly Income")
        self.income_label.setStatusTip("Average Monthly Income")
        self.income_label.setObjectName("income_label")

        self.avg_monthly_income_label = QtWidgets.QLabel(self.income_label)
        self.avg_monthly_income_label.setGeometry(QtCore.QRect(0, 20, 400, 60))
        self.avg_monthly_income_label.setText(f"${self.controller.avg_monthly_income}")
        self.avg_monthly_income_label.setAlignment(QtCore.Qt.AlignCenter)
        self.avg_monthly_income_label.setStatusTip("Average Monthly Income")
        self.avg_monthly_income_label.setObjectName("avg_monthly_income_label")

        self.save_budget_button = QtWidgets.QPushButton(self)
        self.save_budget_button.setGeometry(QtCore.QRect(900, 800, 250, 50))
        self.save_budget_button.setObjectName("save_budget_button")
        self.save_budget_button.setText("Save Changes")
        self.save_budget_button.setShortcut("Ctrl+S+B")
        self.save_budget_button.clicked.connect(
            self.controller.save_budget
        )

        self.back_button = QtWidgets
        self.back_button = QtWidgets.QPushButton(self)
        self.back_button.setGeometry(QtCore.QRect(450, 800, 250, 50))
        self.back_button.setText("Back")
        self.back_button.setStatusTip("Go to Last page")
        self.back_button.clicked.connect(
            lambda : self.controller.show_last_page()
        )
        self.back_button.setShortcut("Backspace")

        # load sliders for each budget category depending on the categories in
        # the self/config file
        self.slider_dict = {}
        self.label_dict = {}
        self.percent_dict = {}
        self.dollar_dict = {}
        space_for_slider = int(round(1600 / (len(self.controller.config.ALL_CATEGORIES) - 1), 0))
        count = 0
        for category in list(self.controller.config.ALL_CATEGORIES.keys()):
            if category == "Income":
                continue
            else:
                start = (count * space_for_slider) + (0.5 * space_for_slider)
                self.label_dict[category] = QtWidgets.QLabel(self)
                self.label_dict[category].setGeometry(QtCore.QRect(
                    start, 250, space_for_slider, 50
                    ))
                # self.label_dict[category].setAlignment(QtCore.Qt.AlignCenter)
                self.label_dict[category].setText(category)

                self.percent_dict[category] = QtWidgets.QLabel(self)
                self.percent_dict[category].setGeometry(QtCore.QRect(
                    start, 660, space_for_slider, 40
                ))
                # self.percent_dict[category].setAlignment(QtCore.Qt.AlignCenter)
                category_percent = self.controller.last_budget[category]
                self.percent_dict[category].setText(f"{category_percent}%")

                self.dollar_dict[category] = QtWidgets.QLabel(self)
                self.dollar_dict[category].setGeometry(QtCore.QRect(
                    start, 700, space_for_slider, 40
                ))
                # self.dollar_dict[category].setAlignment(QtCore.Qt.AlignCenter)
                category_dollars = round(category_percent / 100 * self.controller.avg_monthly_income, 2)
                self.dollar_dict[category].setText(f"${category_dollars}")

                self.slider_dict[category] = QtWidgets.QSlider(self)
                self.slider_dict[category].setGeometry(QtCore.QRect(start, 300, 50, 350))
                self.slider_dict[category].setOrientation(QtCore.Qt.Vertical)
                self.slider_dict[category].setRange(0, 100)
                self.slider_dict[category].setValue(self.controller.last_budget[category])
                self.slider_dict[category].valueChanged.connect(
                    self.update_labels
                )
                self.slider_dict[category].setObjectName(f"{category}_slider")

                count += 1

        self.total_percent = QtWidgets.QGroupBox(self)
        self.total_percent.setGeometry(QtCore.QRect(900, 150, 400, 80))
        self.total_percent.setTitle("Percent of Income Used")
        self.total_percent.setStatusTip("Total Percentage of Income Accounted for")
        self.total_percent.setObjectName("total_percent")

        self.total_percent_label = QtWidgets.QLabel(self.total_percent)
        self.total_percent_label.setGeometry(QtCore.QRect(0, 20, 400, 60))
        
        self.total_percent_label.setText(f"{self.find_total_percent()}%")
        self.total_percent_label.setAlignment(QtCore.Qt.AlignCenter)
        self.total_percent_label.setStatusTip("Total Percentage of Income Accounted for")
        self.total_percent_label.setObjectName("total_percent_label")

    def update_labels(self, value):
        category = self.sender().objectName().split("_")[0]
        self.percent_dict[category].setText(f"{round(value, 2)}%")
        self.dollar_dict[category].setText(
            f"${(round(value, 2) / 100) * self.controller.avg_monthly_income}"
            )
        self.total_percent_label.setText(f"{self.find_total_percent()}%")
        
    def find_total_percent(self):
        percent_used = 0
        for category in list(self.controller.config.ALL_CATEGORIES.keys()):
            if category == "Income":
                continue
            else:
                percent_used += self.slider_dict[category].value()
        return percent_used


class Style():
    def __init__(self):
        pass
    #TODO style erythan


if __name__ == "__main__":
    ui = View("")
    ui.setup_ui()
    ui.show_ui()
    

