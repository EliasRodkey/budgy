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
        self.budget_analysis_page = BudgetAnalysisPage(self.controller)
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
        self.stackedWidget.addWidget(self.budget_analysis_page)
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
        self.page_setup()

    def page_setup(self):
        self.setObjectName("Spending Analysis Page")
        self.setStatusTip("Spending Analyzer")

        self.title = QtWidgets.QLabel(self)
        self.title.setGeometry(QtCore.QRect(0, 25, 1600, 150))
        self.title.setText("Spending Analyzer")
        self.title.setStatusTip("Spending Analysis Page")
        self.title.setAlignment(QtCore.Qt.AlignCenter)

        self.chart_type_comboBox = QtWidgets.QComboBox(self)
        self.chart_type_comboBox.setGeometry(QtCore.QRect(230, 200, 300, 50))
        self.chart_type_comboBox.setObjectName("chart_type_comboBox")
        self.chart_type_comboBox.addItem("")
        self.chart_type_comboBox.addItem("")
        self.chart_type_comboBox.addItem("")
        self.chart_type_comboBox.setItemText(0, "Chart Type")
        self.chart_type_comboBox.setItemText(1, "Line")
        self.chart_type_comboBox.setItemText(2, "Pie")
        self.chart_type_comboBox.setStatusTip("Choose Chart Type")

        self.time_period_combobox = QtWidgets.QComboBox(self)
        self.time_period_combobox.setGeometry(QtCore.QRect(630, 200, 300, 50))
        self.time_period_combobox.setObjectName("time_period_combobox")
        self.time_period_combobox.addItem("")
        self.time_period_combobox.addItem("")
        self.time_period_combobox.addItem("")
        self.time_period_combobox.addItem("")
        self.time_period_combobox.addItem("")
        self.time_period_combobox.setItemText(0, "Time Breakdown")
        self.time_period_combobox.setItemText(1, "All")
        self.time_period_combobox.setItemText(2, "Years")
        self.time_period_combobox.setItemText(3, "Months")
        self.time_period_combobox.setItemText(4, "Weeks")
        self.time_period_combobox.setStatusTip("Choose Time Breakdown Type")

        self.sub_category_combobox = QtWidgets.QComboBox(self)
        self.sub_category_combobox.setGeometry(QtCore.QRect(1030, 200, 300, 50))
        self.sub_category_combobox.setObjectName("sub_category_combobox")
        self.sub_category_combobox.addItem("")
        self.sub_category_combobox.setItemText(0, "Sub Category")
        self.sub_category_combobox.setStatusTip("Choose Sub Category for Analysis")

        self.date_range_box = QtWidgets.QGroupBox(self)
        self.date_range_box.setGeometry(QtCore.QRect(230, 270, 1100, 110))
        self.date_range_box.setObjectName("date_range_box")
        self.date_range_box.setTitle("Date Range")
        self.date_range_box.setStatusTip("Choose Date Range of Analysis")

        self.start_date = QtWidgets.QDateEdit(self.date_range_box)
        self.start_date.setGeometry(QtCore.QRect(200, 40, 300, 50))
        self.start_date.setObjectName("start_date")
        self.start_date.setStatusTip("Choose Start Date of Analysis")

        self.end_date = QtWidgets.QDateEdit(self.date_range_box)
        self.end_date.setGeometry(QtCore.QRect(750, 40, 300, 50))
        self.end_date.setObjectName("end_date")
        self.end_date.setStatusTip("Choose End Date of Analysis")

        self.from_label = QtWidgets.QLabel(self.date_range_box)
        self.from_label.setGeometry(QtCore.QRect(50, 40, 100, 50))
        self.from_label.setObjectName("from_label")
        self.from_label.setText("From:")
        self.from_label.setAlignment(QtCore.Qt.AlignCenter)
        self.from_label.setStatusTip("Choose Start Date of Analysis")

        self.to_label = QtWidgets.QLabel(self.date_range_box)
        self.to_label.setGeometry(QtCore.QRect(600, 40, 100, 50))
        self.to_label.setObjectName("to_label")
        self.to_label.setText("To:")
        self.to_label.setAlignment(QtCore.Qt.AlignCenter)
        self.to_label.setStatusTip("Choose End Date of Analysis")

        # self.see_analysis_button = QtWidgets.QPushButton(self)
        # self.see_analysis_button.set_geometry

        self.to_budget_analysis_button = QtWidgets
        self.to_budget_analysis_button = QtWidgets.QPushButton(self)
        self.to_budget_analysis_button.setGeometry(QtCore.QRect(675, 800, 250, 50))
        self.to_budget_analysis_button.setText("Budget Analysis")
        self.to_budget_analysis_button.setStatusTip("Go to Spending Analysis")
        self.to_budget_analysis_button.clicked.connect(
            lambda : self.controller.show_page(self.controller.view.budget_analysis_page)
        )
        self.to_budget_analysis_button.setShortcut("Right")


class BudgetAnalysisPage(QtWidgets.QWidget):
    def __init__(self, controller):
        self.controller = controller
        super().__init__()
        self.page_setup()

    def page_setup(self):
        self.setObjectName("Budget Analysis Page")
        self.setStatusTip("Budget Analyzer")

        self.title = QtWidgets.QLabel(self)
        self.title.setGeometry(QtCore.QRect(0, 25, 1600, 150))
        self.title.setText("Budget Analyzer")
        self.title.setStatusTip("Budget Analysis Page")
        self.title.setAlignment(QtCore.Qt.AlignCenter)

        self.to_spending_analysis_button = QtWidgets
        self.to_spending_analysis_button = QtWidgets.QPushButton(self)
        self.to_spending_analysis_button.setGeometry(QtCore.QRect(675, 800, 250, 50))
        self.to_spending_analysis_button.setText("Spending Analysis")
        self.to_spending_analysis_button.setStatusTip("Go to Spending Analysis")
        self.to_spending_analysis_button.clicked.connect(
            lambda : self.controller.show_page(self.controller.view.spending_analysis_page)
        )
        self.to_spending_analysis_button.setShortcut("Right")


class BudgetEditPage(QtWidgets.QWidget):
    def __init__(self, controller):
        self.controller = controller
        super().__init__()
        self.page_setup()
    
    def page_setup(self):
        self.setObjectName("Budget Edit Page")
        self.setStatusTip("Budget Goal Editor")

        self.title = QtWidgets.QLabel(self)
        self.title.setGeometry(QtCore.QRect(0, 25, 1600, 150))
        self.title.setText("Budget Setter")
        self.title.setStatusTip("Budget Editing Page")
        self.title.setAlignment(QtCore.Qt.AlignCenter)

        self.save_budget_button = QtWidgets.QPushButton(self)
        self.save_budget_button.setGeometry(QtCore.QRect(180, 280, 75, 23))
        self.save_budget_button.setObjectName("save_budget_button")
        self.save_budget_button.setText("Save Changes")
        self.save_budget_button.setShortcut("Ctrl+S+B")

        self.to_spending_analysis_button = QtWidgets
        self.to_spending_analysis_button = QtWidgets.QPushButton(self)
        self.to_spending_analysis_button.setGeometry(QtCore.QRect(675, 800, 250, 50))
        self.to_spending_analysis_button.setText("Back")
        self.to_spending_analysis_button.setStatusTip("Go to Last page")
        self.to_spending_analysis_button.clicked.connect(
            lambda : self.controller.show_page(self.controller.view.title_page)
        )
        self.to_spending_analysis_button.setShortcut("Backspace")
    
    def make_category_slider(self, category):
        self.verticalSlider = QtWidgets.QSlider(self)
        self.verticalSlider.setGeometry(QtCore.QRect(40, 50, 16, 160))
        self.verticalSlider.setOrientation(QtCore.Qt.Vertical)
        self.verticalSlider.setObjectName(f"{category}_slider")


class Style():
    def __init__(self):
        pass
    #TODO style erythan


if __name__ == "__main__":
    ui = View("")
    ui.setup_ui()
    ui.show_ui()
    

