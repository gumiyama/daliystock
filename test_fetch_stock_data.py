import unittest
import os
import pandas as pd
import shutil # For cleaning up directory

# Assuming fetch_stock_data.py is in the same directory or accessible in PYTHONPATH
from fetch_stock_data import main as fetch_main

class TestFetchStockData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up for all tests in this class."""
        cls.test_stock_codes = ["1301.T", "7203.T"] # Toyota and Kyokuyo
        cls.test_data_dir = "stock_data_test"
        cls.test_target_csv = os.path.join(cls.test_data_dir, "all_stocks_data_test.csv")

        # Create the test directory if it doesn't exist
        if not os.path.exists(cls.test_data_dir):
            os.makedirs(cls.test_data_dir)
            print(f"Created test directory: {cls.test_data_dir}")

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests in this class."""
        # Remove the test directory and its contents
        if os.path.exists(cls.test_data_dir):
            shutil.rmtree(cls.test_data_dir)
            print(f"Removed test directory: {cls.test_data_dir}")

    def setUp(self):
        """Clean up the target CSV before each test method."""
        if os.path.exists(self.test_target_csv):
            os.remove(self.test_target_csv)
            print(f"Removed test CSV: {self.test_target_csv} before a test.")

    def _get_row_counts(self, df):
        """Helper to get row counts per stock and total."""
        counts = {}
        if not df.empty and 'StockCode' in df.columns:
            for stock_code in self.test_stock_codes:
                counts[stock_code] = len(df[df['StockCode'] == stock_code])
        counts['total'] = len(df)
        return counts

    def test_01_initial_fetch_and_file_structure(self):
        """
        Test initial data fetch, file creation, and basic structure.
        """
        print(f"Running test_01_initial_fetch_and_file_structure, outputting to {self.test_target_csv}")
        fetch_main(test_codes=self.test_stock_codes, output_csv_path=self.test_target_csv)

        self.assertTrue(os.path.exists(self.test_target_csv), "CSV file was not created.")
        
        try:
            df = pd.read_csv(self.test_target_csv)
        except pd.errors.EmptyDataError:
            self.fail("CSV file is empty.")
        
        self.assertFalse(df.empty, "CSV file is empty after fetch.")
        self.assertIn('StockCode', df.columns, "'StockCode' column not found in CSV.")
        self.assertIn('Date', df.columns, "'Date' column not found in CSV.")
        self.assertIn('Open', df.columns, "'Open' column not found in CSV.") # Check for typical stock data
        
        fetched_codes = set(df['StockCode'].unique())
        self.assertEqual(set(self.test_stock_codes), fetched_codes, 
                         "Mismatch between requested and fetched stock codes in CSV.")
        
        # Store row counts for the next test if needed, or just for this test's assertions
        # For yfinance, the number of rows can be substantial even for a short period.
        # We primarily check that data for each stock code exists.
        for code in self.test_stock_codes:
            self.assertTrue(len(df[df['StockCode'] == code]) > 0, f"No data found for stock code {code}.")
        
        # Save current state for next potential ordered test (if any)
        # This is tricky as test order is not guaranteed unless named like test_A, test_B
        # For now, each test tries to be somewhat independent or sets up its own state.


    def test_02_differential_update_all_stocks(self):
        """
        Test that running fetch again for all stocks updates differentially.
        """
        print(f"Running test_02_differential_update_all_stocks, outputting to {self.test_target_csv}")
        # First run
        fetch_main(test_codes=self.test_stock_codes, output_csv_path=self.test_target_csv)
        self.assertTrue(os.path.exists(self.test_target_csv), "CSV file was not created on first run.")
        df_run1 = pd.read_csv(self.test_target_csv)
        self.assertFalse(df_run1.empty, "CSV is empty after first run.")
        counts_run1 = self._get_row_counts(df_run1)
        self.assertTrue(counts_run1[self.test_stock_codes[0]] > 0, f"No data for {self.test_stock_codes[0]} in run 1")
        self.assertTrue(counts_run1[self.test_stock_codes[1]] > 0, f"No data for {self.test_stock_codes[1]} in run 1")


        # Second run with the same codes
        print("Running fetch_main for the second time (all stocks)...")
        fetch_main(test_codes=self.test_stock_codes, output_csv_path=self.test_target_csv)
        self.assertTrue(os.path.exists(self.test_target_csv), "CSV file does not exist after second run.")
        df_run2 = pd.read_csv(self.test_target_csv)
        self.assertFalse(df_run2.empty, "CSV is empty after second run.")
        counts_run2 = self._get_row_counts(df_run2)

        # Assertions for differential update
        # Number of rows should be greater than or equal (if new day's data came in)
        # It should not be significantly more (e.g., doubled)
        for code in self.test_stock_codes:
            self.assertGreaterEqual(counts_run2[code], counts_run1[code],
                                    f"Row count for {code} decreased or was not properly appended.")
            # Heuristic: not more than 10 new entries per day usually, for 2 codes, not more than 20-30 new rows total than original.
            # If yfinance returns full history on a failed delta, this would catch it.
            self.assertLess(counts_run2[code], counts_run1[code] * 1.5 if counts_run1[code] > 0 else 200, # Allow some growth, or initial fetch size if prev was 0
                            f"Row count for {code} increased excessively, suggesting non-differential update.")

        self.assertGreaterEqual(counts_run2['total'], counts_run1['total'])
        self.assertLess(counts_run2['total'], counts_run1['total'] * 1.5 if counts_run1['total'] > 0 else 400,
                        "Total row count increased excessively.")
        self.assertEqual(set(self.test_stock_codes), set(df_run2['StockCode'].unique()),
                         "Stock codes in CSV changed after second run.")

    def test_03_differential_update_single_stock(self):
        """
        Test that running fetch for a single stock only updates that stock's data.
        """
        print(f"Running test_03_differential_update_single_stock, outputting to {self.test_target_csv}")
        # Initial run with all test stocks
        fetch_main(test_codes=self.test_stock_codes, output_csv_path=self.test_target_csv)
        df_run1 = pd.read_csv(self.test_target_csv)
        counts_run1 = self._get_row_counts(df_run1)
        
        self.assertTrue(counts_run1[self.test_stock_codes[0]] > 0, f"No data for {self.test_stock_codes[0]} in run 1")
        self.assertTrue(counts_run1[self.test_stock_codes[1]] > 0, f"No data for {self.test_stock_codes[1]} in run 1")

        # Second run with only the first stock code
        single_test_code = [self.test_stock_codes[0]]
        print(f"Running fetch_main for the second time (single stock: {single_test_code[0]})...")
        fetch_main(test_codes=single_test_code, output_csv_path=self.test_target_csv)
        df_run2 = pd.read_csv(self.test_target_csv)
        counts_run2 = self._get_row_counts(df_run2)

        # Check the updated stock
        self.assertGreaterEqual(counts_run2[single_test_code[0]], counts_run1[single_test_code[0]],
                                f"Row count for updated stock {single_test_code[0]} should not decrease.")
        self.assertLess(counts_run2[single_test_code[0]], counts_run1[single_test_code[0]] * 1.5 if counts_run1[single_test_code[0]] > 0 else 200,
                        f"Row count for updated stock {single_test_code[0]} increased excessively.")

        # Check the stock that was not part of the second run
        # Its row count should remain exactly the same.
        other_stock_code = self.test_stock_codes[1]
        self.assertEqual(counts_run2[other_stock_code], counts_run1[other_stock_code],
                         f"Row count for non-updated stock {other_stock_code} changed.")
        
        # Ensure overall structure remains valid
        self.assertEqual(set(self.test_stock_codes), set(df_run2['StockCode'].unique()),
                         "Set of unique stock codes in CSV changed unexpectedly.")

if __name__ == '__main__':
    unittest.main()
