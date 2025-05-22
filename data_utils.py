"""
Utility functions for handling data, particularly stock data.
"""

import pandas as pd
import os

def load_stock_data(ticker, data_dir="stock_data"):
    """
    Loads stock data from a CSV file, processes dates, and adds time-based features.

    Args:
        ticker (str): The stock ticker symbol (e.g., "7203.T").
        data_dir (str, optional): The directory containing the stock data CSV files.
                                Defaults to "stock_data".

    Returns:
        pandas.DataFrame or None: The processed DataFrame if successful, otherwise None.
    """
    file_path = os.path.join(data_dir, f"{ticker}.csv")

    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error reading or processing file {file_path}: {e}")
        return None

    # Parse 'Date' column
    if 'Date' not in df.columns:
        print(f"Error: 'Date' column not found in {file_path}")
        return None
    try:
        df['Date'] = pd.to_datetime(df['Date'])
    except Exception as e:
        print(f"Error parsing 'Date' column in {file_path}: {e}")
        return None

    # Add time-based features
    try:
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        df['Quarter'] = df['Date'].dt.quarter
        df['DayOfWeek'] = df['Date'].dt.dayofweek
        df['WeekOfYear'] = df['Date'].dt.isocalendar().week.astype(int) # Ensure week is int
    except Exception as e:
        print(f"Error creating time-based features for {file_path}: {e}")
        return None

    return df
