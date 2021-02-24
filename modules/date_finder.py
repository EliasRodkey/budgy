#! python3
# date_finder.py - uses the user input dates to find various
# useful date ranges such as past week, 2 weeks, month, 3 months
# 6 months, all date ranges for weeks, months, and years that will
# be used in the table constructor
import logging

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)

import calendar
import datetime
from random import randint

def datetimes_to_range(datetimes):
    old_date = datetimes["start"].strftime("%m/%d/%Y")
    new_date = datetimes["end"].strftime("%m/%d/%Y")
    return f"{old_date} - {new_date}"


class DateFinder():
    def __init__(self, input_start_date, input_end_date):
        # create lists of weeks and a list of months and years to filter by later
        self.now = datetime.datetime.now()
        self.all_time_dates = {
            "start" : input_start_date, 
            "end" : input_end_date
        }
        self.all = [
            f"{self.all_time_dates['start'].strftime('%m/%d/%Y')} - {self.all_time_dates['end'].strftime('%m/%d/%Y')}"
            ]
        self.years = self.find_years(self.all_time_dates)
        self.one_year_today = self.find_year_from_today()
        self.months = self.find_months(self.all_time_dates)
        self.one_month_today = self.find_month_from_today(1)
        self.three_months_today = self.find_month_from_today(3)
        self.six_months_today = self.find_month_from_today(6)
        self.weeks = self.find_weeks()
        self.one_week_toady = self.find_weeks_from_today(1)
        self.two_week_toady = self.find_weeks_from_today(2)
        self.three_week_toady = self.find_weeks_from_today(3)
        self.six_week_toady = self.find_weeks_from_today(6)

    # returns the start and end dates of each year in the transactions history
    def find_years(self, all_time_range):
        start = all_time_range["start"].year
        end = all_time_range["end"].year
        years_passed = end - start
        years = []
        for i in range(years_passed + 1):
            current = start + i
            years.append(f"01/01/{current} - 12/31/{current}")
        years = self.sort_dates(years)
        return years
    
    # returns range of this date a year ago to current date
    def find_year_from_today(self):
        year = self.now.year - 1
        year_ago = datetime.date(year, self.now.month, self.now.day)
        rang = datetimes_to_range({"start":year_ago, "end" : self.now})
        return [rang]

    # finds all of the months with transactions returned in a list of tuples
    def find_months(self, all_time_range):
        months = []
        current = all_time_range["start"]
        while current <= all_time_range["end"]:
            last_day = calendar.monthrange(current.year, current.month)[1]
            range_string = f"{current.strftime('%m/01/%Y')} - {current.strftime(f'%m/{last_day}/%Y')}"
            if range_string not in months:
                months.append(range_string)
            current += datetime.timedelta(days=6)
        months = self.sort_dates(months)
        return months
    
    # finds designated of months going back from today
    # a months is defined as 30 days for the purposes of this function
    def find_month_from_today(self, months:int):
        time_delta = datetime.timedelta(days=30*months)
        month_ago = self.now - time_delta
        rang = datetimes_to_range({"start" : month_ago, "end" : self.now})
        return [rang]
    
    # finds all the weeks (7 day periods) from first transaction until the 
    # beginning of transaciton hsitory
    def find_weeks(self):
        weeks = []
        for month in self.months:
            month = month.split(" - ")[0]
            month_num = datetime.datetime.strptime(month, "%m/%d/%Y")
            raw_weeks = calendar.Calendar().monthdatescalendar(
                month_num.year, month_num.month
                )
            for week in raw_weeks:
                rang = f"{week[0].strftime('%m/%d/%Y')} - {week[-1].strftime('%m/%d/%Y')}"
                if rang not in weeks:
                    weeks.append(rang)
        weeks = self.sort_dates(weeks)
        return weeks
    
    def find_weeks_from_today(self, weeks:int):
        time_delta = datetime.timedelta(days=7*weeks)
        week_ago = self.now - time_delta
        rang = datetimes_to_range({"start" : week_ago, "end" : self.now})
        return [rang]

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

if __name__ == "__main__":
    start = datetime.date(2019, 3, 26)
    end = datetime.date(2021, 2, 23)
    dates = DateFinder(start, end)
    import pprint
    pprint.pprint(dates.one_week_toady)