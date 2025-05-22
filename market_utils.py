"""
Utility functions for market-related operations, such as handling business days and holidays.
"""

import holidays
from datetime import datetime, date
import pandas as pd
from pandas.tseries.offsets import CustomBusinessDay

def get_japanese_holidays(year_start, year_end):
    """
    Retrieves a set of Japanese holidays for a given year range.

    Args:
        year_start (int): The starting year.
        year_end (int): The ending year.

    Returns:
        set: A set of datetime.date objects representing Japanese holidays.
    """
    jp_holidays = holidays.JP(years=range(year_start, year_end + 1))
    # The holidays.CountryHoliday object jp_holidays is a dict {date: name}.
    # We only need the dates.
    return set(jp_holidays.keys())

def get_next_business_day(input_date_str, country_holidays):
    """
    Calculates the next business day after a given date, considering weekends and holidays.

    Args:
        input_date_str (str): The starting date in "YYYY-MM-DD" format.
        country_holidays (set): A set of datetime.date objects representing holidays.

    Returns:
        datetime.date: The next business day.
    """
    try:
        # Convert input_date_str to datetime.date object
        start_date = datetime.strptime(input_date_str, "%Y-%m-%d").date()
    except ValueError:
        print(f"Error: Invalid date format for input_date_str. Please use YYYY-MM-DD.")
        return None

    # Define a custom business day rule, excluding weekends and specified holidays
    # The holidays need to be in a format that CustomBusinessDay understands,
    # typically a list of datetime.date or pandas.Timestamp objects.
    # Since country_holidays is already a set of datetime.date objects, it should work.
    business_day_rule = CustomBusinessDay(holidays=list(country_holidays))

    # Calculate the next business day
    # .rollforward() moves to the next business day if current date is not a business day
    # or stays on current date if it is a business day.
    # To ensure we get the *next* business day, we first add one calendar day,
    # then rollforward.
    next_day_candidate = pd.Timestamp(start_date) + pd.Timedelta(days=1)
    next_bday_timestamp = business_day_rule.rollforward(next_day_candidate)

    return next_bday_timestamp.date()
