import unittest
import pandas as pd
from datetime import datetime
# Assuming pattern_analyzer.py and data_utils.py are in the root or PYTHONPATH
from pattern_analyzer import (
    analyze_day_of_week_patterns,
    analyze_weekly_patterns,
    analyze_monthly_patterns,
    analyze_quarterly_patterns
)
# data_utils.load_stock_data is for loading from CSV,
# for tests, it's better to construct DataFrames directly.

class TestPatternAnalyzer(unittest.TestCase):

    def setUp(self):
        # Sample data for Day of Week tests
        self.dow_data = pd.DataFrame({
            'Date': pd.to_datetime([
                '2023-10-02', '2023-10-03', '2023-10-04', '2023-10-05', '2023-10-06', # Week 1
                '2023-10-09', '2023-10-10', '2023-10-11', '2023-10-12', '2023-10-13', # Week 2
                '2023-10-16', '2023-10-17'                                          # Week 3 (partial)
            ]),
            'Close': [
                100, 101, 102, 103, 90,  # Week 1 (Mon buy, Tue profit; Mon buy, Fri loss)
                110, 111, 112, 113, 114, # Week 2 (Mon buy, Tue profit; Mon buy, Fri profit)
                120, 121                 # Week 3 (Mon buy, Tue profit)
            ],
            'DayOfWeek': [
                0, 1, 2, 3, 4,  # Mon, Tue, Wed, Thu, Fri
                0, 1, 2, 3, 4,  # Mon, Tue, Wed, Thu, Fri
                0, 1            # Mon, Tue
            ]
        })

        # Sample data for Weekly, Monthly, Quarterly tests
        self.time_series_data = pd.DataFrame({
            'Date': pd.to_datetime([
                # 2023
                '2023-01-02', '2023-01-09', '2023-01-16', '2023-01-23', '2023-01-30', # Jan, Weeks 1-5
                '2023-02-06', '2023-02-13', '2023-02-20', '2023-02-27',             # Feb, Weeks 6-9
                '2023-03-06', '2023-03-13', '2023-03-20', '2023-03-27',             # Mar, Weeks 10-13 (Q1 ends)
                '2023-04-03', '2023-04-10', '2023-04-17', '2023-04-24',             # Apr, Weeks 14-17
                '2023-09-25', # Week 39 (Sep)
                '2023-10-02', # Week 40 (Oct)
                '2023-10-09', # Week 41 (Oct)
                '2023-10-16', # Week 42 (Oct)
            ]),
            'Close': [
                100, 101, 102, 103, 104, # Jan
                105, 106, 107, 108,     # Feb
                109, 110, 111, 112,     # Mar
                113, 114, 115, 116,     # Apr
                150, # W39
                160, # W40 - Buy for weekly test
                170, # W41 - Sell for weekly test (profit)
                180, # W42
            ]
        })
        # Add required time features
        self.time_series_data['Year'] = self.time_series_data['Date'].dt.year
        self.time_series_data['Month'] = self.time_series_data['Date'].dt.month
        self.time_series_data['Quarter'] = self.time_series_data['Date'].dt.quarter
        self.time_series_data['WeekOfYear'] = self.time_series_data['Date'].dt.isocalendar().week.astype(int)
        self.time_series_data['DayOfWeek'] = self.time_series_data['Date'].dt.dayofweek


    # --- Tests for analyze_day_of_week_patterns ---
    def test_dow_buy_monday_sell_next_day_profit(self):
        # Buy Mon (0), hold 1 day (sell Tue)
        # W1: 100 -> 101 (Profit)
        # W2: 110 -> 111 (Profit)
        # W3: 120 -> 121 (Profit)
        prob, occ = analyze_day_of_week_patterns(self.dow_data, buy_day_of_week=0, hold_trading_days=1)
        self.assertEqual(occ, 3)
        self.assertEqual(prob, 1.0)

    def test_dow_buy_monday_sell_friday_loss_and_profit(self):
        # Buy Mon (0), hold 4 days (sell Fri)
        # W1: 100 -> 90 (Loss)
        # W2: 110 -> 114 (Profit)
        # W3: Mon 120, but no Friday data for this one
        prob, occ = analyze_day_of_week_patterns(self.dow_data, buy_day_of_week=0, hold_trading_days=4)
        self.assertEqual(occ, 2) # Only two Mondays have a corresponding Friday 4 days later
        self.assertEqual(prob, 0.5) # 1 profit, 1 loss

    def test_dow_no_buy_signals(self):
        # Buy on Saturday (5), data only has Mon-Fri
        prob, occ = analyze_day_of_week_patterns(self.dow_data, buy_day_of_week=5, hold_trading_days=1)
        self.assertEqual(occ, 0)
        self.assertEqual(prob, 0)

    def test_dow_insufficient_data_for_hold(self):
        # Buy Mon, hold 10 days. Data is too short.
        # W1: Mon 100. 10 days later is outside data.
        # W2: Mon 110. 10 days later is outside data.
        # W3: Mon 120. 10 days later is outside data.
        # All 3 Mondays are buy signals, but none can be sold.
        prob, occ = analyze_day_of_week_patterns(self.dow_data, buy_day_of_week=0, hold_trading_days=10)
        self.assertEqual(occ, 3) # 3 buy signals found
        self.assertEqual(prob, 0) # 0 successful trades as no sell can occur

    # --- Tests for analyze_weekly_patterns ---
    def test_weekly_buy_week_x_sell_y_weeks_later_profit(self):
        # Buy Week 40 (Close 160), hold 1 week, sell Week 41 (Close 170) -> Profit
        # Only one year of data (2023)
        prob, occ = analyze_weekly_patterns(self.time_series_data, buy_week_of_year=40, hold_weeks=1)
        self.assertEqual(occ, 1) # One occurrence of buying in week 40
        self.assertEqual(prob, 1.0) # It was profitable

    def test_weekly_buy_week_insufficient_data_for_sell(self):
        # Buy Week 42, hold 1 week. No data for Week 43.
        prob, occ = analyze_weekly_patterns(self.time_series_data, buy_week_of_year=42, hold_weeks=1)
        self.assertEqual(occ, 1) # Buy signal found for week 42
        self.assertEqual(prob, 0) # No successful trade as sell week data is missing

    # --- Test for missing columns ---
    def test_missing_close_column_day_of_week(self):
        bad_df = self.dow_data.drop(columns=['Close'])
        prob, occ = analyze_day_of_week_patterns(bad_df, buy_day_of_week=0, hold_trading_days=1)
        self.assertEqual(occ, 0)
        self.assertEqual(prob, 0)
        # The function should print an error, which we can't directly test here without more complex mocking.

    def test_missing_dayofweek_column_day_of_week(self):
        bad_df = self.dow_data.drop(columns=['DayOfWeek'])
        prob, occ = analyze_day_of_week_patterns(bad_df, buy_day_of_week=0, hold_trading_days=1)
        self.assertEqual(occ, 0)
        self.assertEqual(prob, 0)

    def test_missing_weekofyear_column_weekly(self):
        bad_df = self.time_series_data.drop(columns=['WeekOfYear'])
        prob, occ = analyze_weekly_patterns(bad_df, buy_week_of_year=40, hold_weeks=1)
        self.assertEqual(occ, 0)
        self.assertEqual(prob, 0)

    # --- Basic tests for monthly and quarterly to ensure they run ---
    def test_monthly_pattern_runs(self):
        # Buy Jan (1), hold 1 month (sell Feb)
        # 2023: Jan close 100 (first day), Feb close 105 (first day) -> Profit
        prob, occ = analyze_monthly_patterns(self.time_series_data, buy_month=1, hold_months=1)
        self.assertEqual(occ, 1)
        self.assertEqual(prob, 1.0)

    def test_quarterly_pattern_runs(self):
        # Buy Q1 (Jan), hold 1 quarter (sell Q2 - Apr)
        # 2023: Q1 Jan close 100, Q2 Apr close 113 -> Profit
        prob, occ = analyze_quarterly_patterns(self.time_series_data, buy_quarter=1, hold_quarters=1)
        self.assertEqual(occ, 1)
        self.assertEqual(prob, 1.0)


if __name__ == '__main__':
    unittest.main()
