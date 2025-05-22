import unittest
import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal
from datetime import datetime, date, timedelta
import io
from unittest.mock import patch, MagicMock

# Assuming analyze_seasonality.py is in the same directory or accessible in PYTHONPATH
from analyze_seasonality import (
    load_and_preprocess_data,
    analyze_quarterly_seasonality,
    suggest_trades_for_next_business_day
)

class TestAnalyzeSeasonality(unittest.TestCase):

    # --- Tests for load_and_preprocess_data ---
    def test_load_normal_csv_string(self):
        csv_data = (
            "Date,StockCode,Open,Close,High,Low,Volume\n"
            "2023-01-02,STOCKA,100,102,103,99,1000\n"
            "2023-04-01,STOCKA,105,107,108,104,1200\n"
            "2023-01-03,STOCKB,200,202,203,199,2000\n"
        )
        # Use a unique path for each test that simulates a file to avoid interference
        mock_file_path = "mock_dir/normal_data.csv"

        with patch('pandas.read_csv', return_value=pd.read_csv(io.StringIO(csv_data))) as mock_read_csv:
            df = load_and_preprocess_data(mock_file_path) # Path doesn't matter due to mock

        self.assertIsNotNone(df)
        self.assertEqual(len(df), 3)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df['Date']))
        self.assertEqual(df.loc[0, 'Year'], 2023)
        self.assertEqual(df.loc[0, 'Month'], 1)
        self.assertEqual(df.loc[0, 'Quarter'], 1) # (1-1)//3 + 1
        self.assertEqual(df.loc[0, 'DayOfWeek'], 0) # 2023-01-02 is a Monday
        self.assertEqual(df.loc[1, 'Quarter'], 2) # (4-1)//3 + 1

    @patch('builtins.open', side_effect=FileNotFoundError)
    @patch('pandas.read_csv', side_effect=FileNotFoundError) # Also mock read_csv if open isn't the direct fail point
    def test_load_file_not_found(self, mock_read_csv, mock_open):
        # The print statement in the function will indicate the error
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            df = load_and_preprocess_data("non_existent_file.csv")
        self.assertIsNone(df)
        self.assertIn("Error: The file non_existent_file.csv was not found.", mock_stdout.getvalue())

    def test_load_missing_date_column(self):
        csv_data = "StockCode,Open,Close\nSTOCKA,100,102"
        mock_file_path = "mock_dir/missing_date_data.csv"
        with patch('pandas.read_csv', return_value=pd.read_csv(io.StringIO(csv_data))):
            with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                df = load_and_preprocess_data(mock_file_path)
        self.assertIsNone(df)
        self.assertIn("Error: 'Date' column not found", mock_stdout.getvalue())

    def test_load_invalid_date_format(self):
        csv_data = "Date,StockCode\nInvalidDate,STOCKA\n2023-01-01,STOCKB"
        mock_file_path = "mock_dir/invalid_date_data.csv"
        with patch('pandas.read_csv', return_value=pd.read_csv(io.StringIO(csv_data))):
            with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                df = load_and_preprocess_data(mock_file_path)
        self.assertIsNotNone(df) # Function might return df with NaT
        self.assertTrue(df['Date'].isnull().any()) # Check for NaT
        self.assertIn("Warning: Some 'Date' values could not be parsed", mock_stdout.getvalue())
        self.assertEqual(df.loc[1, 'Year'], 2023) # Valid date should still be processed


    # --- Tests for analyze_quarterly_seasonality ---
    def _create_sample_processed_df(self):
        data = {
            'Date': pd.to_datetime([
                '2022-01-03', '2022-03-28', # STOCKA Q1 2022
                '2022-04-04', '2022-06-27', # STOCKA Q2 2022
                '2022-01-03', '2022-03-28', # STOCKB Q1 2022 (same dates, different prices)
                '2023-01-02', '2023-03-29', # STOCKA Q1 2023
                '2023-04-03', '2023-06-29', # STOCKA Q2 2023 (for Q1_to_Q2)
                '2022-07-01', '2022-09-28', # STOCKC Q3 2022 (single quarter data)
                '2022-10-03', '2022-12-28', # STOCKD Q4 2022 (for Q4_to_Q1 transition)
                '2023-01-02', '2023-03-29', # STOCKD Q1 2023 (target for Q4_to_Q1)
                '2022-01-03', '2022-01-30', # STOCKE Q1 2022 (Open price zero test)
            ]),
            'StockCode': [
                'STOCKA', 'STOCKA', 'STOCKA', 'STOCKA',
                'STOCKB', 'STOCKB', 'STOCKA', 'STOCKA',
                'STOCKA', 'STOCKA', 'STOCKC', 'STOCKC',
                'STOCKD', 'STOCKD', 'STOCKD', 'STOCKD',
                'STOCKE', 'STOCKE'
            ],
            'Open': [
                100, 100, 110, 110, # STOCKA Q1, Q2 2022
                200, 200, # STOCKB Q1 2022
                120, 120, 130, 130, # STOCKA Q1, Q2 2023
                300, 300, # STOCKC Q3 2022
                400, 400, 420, 420, # STOCKD Q4 2022, Q1 2023
                0, 0 # STOCKE Q1 2022 (Open price zero)
            ],
            'Close': [
                105, 105, 108, 112, # STOCKA Q1 (+5%), Q2 (+1.8% from 110, or +3.6% from Q2 Open)
                190, 190, # STOCKB Q1 (-5%)
                125, 125, 135, 140, # STOCKA Q1 (+4.16%), Q2 (+3.8% from 130 or +7.6% from Q2 Open)
                303, 303, # STOCKC Q3 (+1%)
                410, 410, 430, 430, # STOCKD Q4 (+2.5%), Q1 (+2.38% from 420)
                10, 10 # STOCKE Q1 (Open price zero)
            ]
        }
        df = pd.DataFrame(data)
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        df['Quarter'] = (df['Month'] - 1) // 3 + 1
        df['DayOfWeek'] = df['Date'].dt.dayofweek
        return df

    def test_quarterly_same_quarter_profitability(self):
        df = self._create_sample_processed_df()
        summary_df = analyze_quarterly_seasonality(df)
        self.assertIsNotNone(summary_df)

        # STOCKA Q1: 2022: (105-100)/100 = 0.05. 2023: (125-120)/120 = 0.041666...
        # Avg for STOCKA, Q1_Same = (0.05 + 0.041666) / 2 = 0.045833
        stocka_q1_same = summary_df[
            (summary_df['StockCode'] == 'STOCKA') & (summary_df['PatternType'] == 'Q1_Same')
        ]
        self.assertEqual(len(stocka_q1_same), 1)
        self.assertAlmostEqual(stocka_q1_same['AverageProfitability'].iloc[0], (0.05 + (125-120)/120) / 2, places=5)

        # STOCKB Q1: (190-200)/200 = -0.05
        stockb_q1_same = summary_df[
            (summary_df['StockCode'] == 'STOCKB') & (summary_df['PatternType'] == 'Q1_Same')
        ]
        self.assertEqual(len(stockb_q1_same), 1)
        self.assertAlmostEqual(stockb_q1_same['AverageProfitability'].iloc[0], -0.05, places=5)

    def test_quarterly_next_quarter_profitability(self):
        df = self._create_sample_processed_df()
        summary_df = analyze_quarterly_seasonality(df)
        # STOCKA Q1_to_Q2 for 2022: Entry Q1 2022 (Open 100), Exit Q2 2022 (Close 112) -> (112-100)/100 = 0.12
        # STOCKA Q1_to_Q2 for 2023: Entry Q1 2023 (Open 120), Exit Q2 2023 (Close 140) -> (140-120)/120 = 0.1666...
        # Avg = (0.12 + 0.166666) / 2 = 0.143333
        stocka_q1_to_q2 = summary_df[
            (summary_df['StockCode'] == 'STOCKA') & (summary_df['PatternType'] == 'Q1_to_Q2')
        ]
        self.assertEqual(len(stocka_q1_to_q2), 1)
        self.assertAlmostEqual(stocka_q1_to_q2['AverageProfitability'].iloc[0], (0.12 + (140-120)/120) / 2, places=5)
        
        # STOCKD Q4_to_Q1 (2022 to 2023): Entry Q4 2022 (Open 400), Exit Q1 2023 (Close 430) -> (430-400)/400 = 0.075
        stockd_q4_to_q1 = summary_df[
            (summary_df['StockCode'] == 'STOCKD') & (summary_df['PatternType'] == 'Q4_to_Q1')
        ]
        self.assertEqual(len(stockd_q4_to_q1), 1)
        self.assertAlmostEqual(stockd_q4_to_q1['AverageProfitability'].iloc[0], (430-400)/400, places=5)


    def test_quarterly_edge_case_single_quarter_data(self):
        df = self._create_sample_processed_df()
        summary_df = analyze_quarterly_seasonality(df)
        # STOCKC only has Q3_Same data
        stockc_summary = summary_df[summary_df['StockCode'] == 'STOCKC']
        self.assertEqual(len(stockc_summary), 1)
        self.assertEqual(stockc_summary['PatternType'].iloc[0], 'Q3_Same')
        self.assertAlmostEqual(stockc_summary['AverageProfitability'].iloc[0], (303-300)/300, places=5)

    def test_quarterly_zero_open_price(self):
        df = self._create_sample_processed_df()
        summary_df = analyze_quarterly_seasonality(df)
        # STOCKE has zero open price. Profitability should not be calculated or be NaN/inf,
        # and thus not present in summary if we filter out non-finite values,
        # or the pattern is skipped by `entry_price != 0`
        stocke_summary = summary_df[summary_df['StockCode'] == 'STOCKE']
        # Given `entry_price != 0` in the original code, no records should be generated for STOCKE
        self.assertTrue(stocke_summary.empty, "STOCKE should have no valid profitability records due to zero open price.")

    def test_quarterly_empty_or_none_input(self):
        self.assertIsNone(analyze_quarterly_seasonality(None))
        self.assertIsNone(analyze_quarterly_seasonality(pd.DataFrame()))
        # Test missing required columns
        df_missing_cols = pd.DataFrame({'StockCode': ['A'], 'Date': [datetime(2023,1,1)]}) # Missing Open, Close etc.
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.assertIsNone(analyze_quarterly_seasonality(df_missing_cols))
            self.assertIn("Missing one or more required columns", mock_stdout.getvalue())


    # --- Tests for suggest_trades_for_next_business_day ---
    def _get_mock_date(self, year, month, day):
        mock_date = MagicMock(spec=date)
        mock_date.year = year
        mock_date.month = month
        mock_date.day = day
        mock_date.weekday.return_value = datetime(year, month, day).weekday()
        mock_date.__add__ = lambda self, other: datetime(year,month,day) + other
        mock_date.__sub__ = lambda self, other: datetime(year,month,day) - other
        mock_date.strftime = lambda self, fmt: datetime(year,month,day).strftime(fmt)
        return mock_date

    @patch('analyze_seasonality.datetime') # Mock datetime inside analyze_seasonality module
    def test_suggest_next_bday_calculation(self, mock_dt):
        # Test Friday -> Monday
        mock_dt.today.return_value = self._get_mock_date(2023, 12, 1) # Friday
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            suggest_trades_for_next_business_day(pd.DataFrame()) # Empty df is fine for this part
        self.assertIn("next business day: 2023-12-04", mock_stdout.getvalue())

        # Test Monday -> Tuesday
        mock_dt.today.return_value = self._get_mock_date(2023, 12, 4) # Monday
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            suggest_trades_for_next_business_day(pd.DataFrame())
        self.assertIn("next business day: 2023-12-05", mock_stdout.getvalue())

        # Test Saturday -> Monday
        mock_dt.today.return_value = self._get_mock_date(2023, 12, 2) # Saturday
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            suggest_trades_for_next_business_day(pd.DataFrame())
        self.assertIn("next business day: 2023-12-04", mock_stdout.getvalue())
        
        # Test Sunday -> Monday
        mock_dt.today.return_value = self._get_mock_date(2023, 12, 3) # Sunday
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            suggest_trades_for_next_business_day(pd.DataFrame())
        self.assertIn("next business day: 2023-12-04", mock_stdout.getvalue())


    @patch('analyze_seasonality.datetime')
    def test_suggest_trades_start_of_quarter(self, mock_dt):
        mock_dt.today.return_value = self._get_mock_date(2023, 12, 29) # Friday, next bday is 2024-01-01 (Mon)
                                                                    # if we assume Jan 1st is a business day.
                                                                    # Let's use a date that guarantees it.
                                                                    # Dec 31 2023 is Sunday, so next bday is Jan 1 2024
        mock_dt.today.return_value = self._get_mock_date(2023, 12, 31) # Sunday
        
        sample_summary_data = {
            'StockCode': ['STOCKA', 'STOCKB', 'STOCKC', 'STOCKD'],
            'PatternType': ['Q1_Same', 'Q4_to_Q1', 'Q1_Same', 'Q2_Same'],
            'AverageProfitability': [0.05, 0.08, -0.02, 0.10] # STOCKC Q1_Same is negative
        }
        summary_df = pd.DataFrame(sample_summary_data)

        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            suggest_trades_for_next_business_day(summary_df)
        
        output = mock_stdout.getvalue()
        self.assertIn("next business day: 2024-01-01", output)
        self.assertIn("is potentially the start of Q1", output)
        self.assertIn("Based on 'Q1_Same'", output)
        self.assertIn("- STOCKA (Avg. Profitability: 5.00%)", output)
        self.assertNotIn("- STOCKC", output) # Negative profitability for Q1_Same
        self.assertIn("Based on 'Q4_to_Q1'", output)
        self.assertIn("- STOCKB (Avg. Profitability: 8.00%)", output)
        self.assertNotIn("Q2_Same", output) # Not relevant for Q1 start

    @patch('analyze_seasonality.datetime')
    def test_suggest_trades_not_start_of_quarter(self, mock_dt):
        mock_dt.today.return_value = self._get_mock_date(2023, 2, 15) # Mid-February
        summary_df = pd.DataFrame({
            'StockCode': ['STOCKA'], 'PatternType': ['Q1_Same'], 'AverageProfitability': [0.05]
        })
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            suggest_trades_for_next_business_day(summary_df)
        
        output = mock_stdout.getvalue()
        self.assertIn("next business day: 2023-02-16", output)
        self.assertIn("not considered the start of a quarter (Q1)", output)
        self.assertIn("No quarterly-entry suggestions based on this heuristic", output)

    def test_suggest_trades_empty_summary(self):
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            suggest_trades_for_next_business_day(None)
        self.assertIn("No seasonality summary data available", mock_stdout.getvalue())

        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            suggest_trades_for_next_business_day(pd.DataFrame())
        self.assertIn("No seasonality summary data available", mock_stdout.getvalue())


if __name__ == '__main__':
    unittest.main()
