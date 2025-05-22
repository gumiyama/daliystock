import unittest
import datetime
from market_utils import get_japanese_holidays, get_next_business_day # Assuming market_utils.py is in the root or PYTHONPATH

class TestMarketUtils(unittest.TestCase):

    def test_get_japanese_holidays_specific_year(self):
        holidays_2023 = get_japanese_holidays(2023, 2023)
        self.assertIsInstance(holidays_2023, set)
        
        # Known Japanese holidays in 2023
        self.assertIn(datetime.date(2023, 1, 1), holidays_2023)  # New Year's Day
        self.assertIn(datetime.date(2023, 1, 2), holidays_2023)  # New Year's Holiday / Bank Holiday
        self.assertIn(datetime.date(2023, 1, 9), holidays_2023)  # Coming of Age Day
        self.assertIn(datetime.date(2023, 2, 11), holidays_2023) # National Foundation Day
        self.assertIn(datetime.date(2023, 2, 23), holidays_2023) # Emperor's Birthday
        self.assertIn(datetime.date(2023, 3, 21), holidays_2023) # Vernal Equinox Day
        self.assertIn(datetime.date(2023, 4, 29), holidays_2023) # Showa Day
        self.assertIn(datetime.date(2023, 5, 3), holidays_2023)  # Constitution Memorial Day
        self.assertIn(datetime.date(2023, 5, 4), holidays_2023)  # Greenery Day
        self.assertIn(datetime.date(2023, 5, 5), holidays_2023)  # Children's Day
        self.assertIn(datetime.date(2023, 7, 17), holidays_2023) # Marine Day
        self.assertIn(datetime.date(2023, 8, 11), holidays_2023) # Mountain Day
        self.assertIn(datetime.date(2023, 9, 18), holidays_2023) # Respect for the Aged Day
        self.assertIn(datetime.date(2023, 9, 23), holidays_2023) # Autumnal Equinox Day (approximate, can vary)
        self.assertIn(datetime.date(2023, 10, 9), holidays_2023) # Health and Sports Day
        self.assertIn(datetime.date(2023, 11, 3), holidays_2023) # Culture Day
        self.assertIn(datetime.date(2023, 11, 23), holidays_2023)# Labour Thanksgiving Day

        # Known non-holiday
        self.assertNotIn(datetime.date(2023, 1, 30), holidays_2023) # A regular Monday

    def test_get_next_business_day_weekday(self):
        # Friday, Oct 27, 2023 -> Monday, Oct 30, 2023
        next_bday = get_next_business_day("2023-10-27", []) 
        self.assertEqual(next_bday, datetime.date(2023, 10, 30))

    def test_get_next_business_day_skip_weekend_and_holiday(self):
        # Test with a Friday (2023-11-03, which is Culture Day, a real holiday)
        # and the following Monday (2023-11-06) also a custom holiday.
        # Note: The original prompt had 2023-11-02 (Thu), next bday is 2023-11-03 (Fri, Culture Day)
        # If Friday Nov 3rd is a holiday, next business day is Mon Nov 6th.
        # Let's test with Thursday, Nov 2nd. Next day is Fri Nov 3rd.
        # If Nov 3rd is a holiday, next business day is Mon Nov 6th.
        
        # Scenario: Start Thursday 2023-11-02. Friday 2023-11-03 is a holiday.
        # Expected: Monday 2023-11-06
        holidays = {datetime.date(2023, 11, 3)} # Culture Day
        next_bday = get_next_business_day("2023-11-02", holidays)
        self.assertEqual(next_bday, datetime.date(2023, 11, 6))

        # Scenario from prompt: Start Friday (e.g. 2023-11-03, is a holiday)
        # and the following Monday (2023-11-06) is also a holiday.
        # Expected: Tuesday 2023-11-07
        holidays_complex = {
            datetime.date(2023, 11, 3), # Culture Day (Friday)
            datetime.date(2023, 11, 6)  # Custom holiday (Monday)
        }
        # Starting from Thursday 2023-11-02
        next_bday_complex = get_next_business_day("2023-11-02", holidays_complex)
        self.assertEqual(next_bday_complex, datetime.date(2023, 11, 7))

        # Simpler scenario: Start Friday 2023-07-07. Monday 2023-07-10 is a holiday.
        # Expected: Tuesday 2023-07-11
        holidays_simple = {datetime.date(2023, 7, 10)}
        next_bday_simple = get_next_business_day("2023-07-07", holidays_simple)
        self.assertEqual(next_bday_simple, datetime.date(2023, 7, 11))


    def test_get_next_business_day_current_day_is_holiday(self):
        # Monday, Oct 9, 2023 (Health and Sports Day) -> Tuesday, Oct 10, 2023
        holidays = {datetime.date(2023, 10, 9)}
        # The function finds the *next* business day, so if today is a holiday, it looks for tomorrow onwards.
        next_bday = get_next_business_day("2023-10-09", holidays)
        self.assertEqual(next_bday, datetime.date(2023, 10, 10))
        
        # What if today is a holiday AND tomorrow is also a holiday?
        # E.g., today is Mon (holiday), tomorrow is Tue (holiday) -> Wed
        holidays_multi = {datetime.date(2023, 10, 9), datetime.date(2023, 10, 10)}
        next_bday_multi = get_next_business_day("2023-10-09", holidays_multi)
        self.assertEqual(next_bday_multi, datetime.date(2023, 10, 11))

    def test_get_next_business_day_invalid_date_format(self):
        # market_utils.get_next_business_day returns None on parsing error
        next_bday = get_next_business_day("invalid-date", [])
        self.assertIsNone(next_bday)
        
        next_bday_format = get_next_business_day("2023/10/10", [])
        self.assertIsNone(next_bday_format)

if __name__ == '__main__':
    unittest.main()
