import pandas as pd
import os
import yfinance as yf
import time # Import time for potential delays/rate limiting if needed

def get_stock_codes():
    """
    Fetches stock codes from the JPX website and formats them.

    Returns:
        list: A list of formatted stock codes (e.g., "1301.T")
              or an empty list if an error occurs.
    """
    url = "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls"
    try:
        print("Fetching stock codes from JPX website...")
        df = pd.read_excel(url, skiprows=4, usecols=[1], header=None)
        stock_codes_raw = df.iloc[:, 0]
        valid_codes = []
        for item in stock_codes_raw:
            if pd.notna(item):
                try:
                    code_int = int(item)
                    valid_codes.append(str(code_int))
                except ValueError:
                    pass # Skip non-integer values
        formatted_codes = [code + ".T" for code in valid_codes]
        print(f"Successfully fetched {len(formatted_codes)} stock codes.")
        return formatted_codes
    except Exception as e:
        print(f"Error fetching or processing stock data from JPX: {e}")
        return []

def fetch_and_save_stock_data(stock_code, data_directory="stock_data"):
    """
    Fetches historical stock data for a given stock code using yfinance
    and saves it to a CSV file, performing differential updates.

    Args:
        stock_code (str): The stock code (e.g., "1301.T").
        data_directory (str): The directory to save the stock data CSV files.
    """
    if not os.path.exists(data_directory):
        try:
            os.makedirs(data_directory)
            print(f"Created directory: {data_directory}")
        except Exception as e:
            print(f"Error creating directory {data_directory}: {e}")
            return

    file_path = os.path.join(data_directory, f"{stock_code}.csv")
    start_date = None
    existing_data_df = None
    file_exists = os.path.exists(file_path)

    if file_exists:
        try:
            existing_data_df = pd.read_csv(file_path)
            if not existing_data_df.empty and 'Date' in existing_data_df.columns:
                existing_data_df['Date'] = pd.to_datetime(existing_data_df['Date'])
                latest_date = existing_data_df['Date'].max()
                start_date = (latest_date + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
            else: # File might be empty or 'Date' column missing
                print(f"File {file_path} exists but is empty or 'Date' column missing. Will fetch all data.")
                file_exists = False # Treat as if file doesn't exist for fetching logic
        except Exception as e:
            print(f"Error reading existing file {file_path}: {e}. Will attempt to fetch all data.")
            file_exists = False # Treat as if file doesn't exist for fetching logic
    
    try:
        ticker = yf.Ticker(stock_code)
        new_data_df = ticker.history(start=start_date, auto_adjust=True)

        if new_data_df.empty:
            if start_date:
                print(f"No new data fetched for {stock_code} (start_date: {start_date}).")
            else:
                print(f"No data fetched for {stock_code} (full history attempted). This might be an invalid/delisted code or no data available.")
            return

        new_data_df.reset_index(inplace=True)
        new_data_df['Date'] = pd.to_datetime(new_data_df['Date'])

    except Exception as e:
        print(f"Error fetching data from yfinance for {stock_code}: {e}")
        return

    try:
        if not new_data_df.empty:
            if file_exists and start_date is not None and existing_data_df is not None and not existing_data_df.empty :
                latest_date_in_file = existing_data_df['Date'].max()
                new_data_to_append = new_data_df[new_data_df['Date'] > latest_date_in_file]
                
                if not new_data_to_append.empty:
                    new_data_to_append.to_csv(file_path, mode='a', header=False, index=False)
                    print(f"Appended new data for {stock_code} to {file_path}.")
                else:
                    print(f"No new data to append for {stock_code} after filtering (start_date: {start_date}).")
            else:
                new_data_df.to_csv(file_path, index=False)
                print(f"Saved data for {stock_code} to {file_path}.")
    except Exception as e:
        print(f"Error saving data for {stock_code} to {file_path}: {e}")

def main(specific_tickers=None):
    """
    Main function to orchestrate fetching stock codes and their historical data.

    Args:
        specific_tickers (list, optional): A list of ticker symbols (e.g., ["7203.T"])
                                           to fetch. If None, fetches all JPX codes.
                                           Defaults to None.
    """
    print("Starting the stock data fetching process...")
    
    stock_codes_to_process = []

    if specific_tickers is not None:
        if isinstance(specific_tickers, list) and all(isinstance(t, str) for t in specific_tickers):
            stock_codes_to_process = specific_tickers
            print(f"Processing a specific list of {len(stock_codes_to_process)} tickers.")
        else:
            print("Error: specific_tickers argument must be a list of strings. Exiting.")
            return
    else:
        print("No specific tickers provided, fetching all available JPX stock codes.")
        stock_codes_to_process = get_stock_codes()
        if not stock_codes_to_process:
            print("No stock codes retrieved from JPX. Exiting.")
            return
        print(f"Found {len(stock_codes_to_process)} stock codes from JPX to process.")

    if not stock_codes_to_process: # Final check if list is empty
        print("No stock codes to process. Exiting.")
        return
        
    total_to_process = len(stock_codes_to_process)
    
    for i, code in enumerate(stock_codes_to_process):
        print(f"\nProcessing stock {i+1} of {total_to_process}: {code}")
        fetch_and_save_stock_data(code, data_directory="stock_data")
        # Optional: Add a small delay to avoid overwhelming the server
        # time.sleep(0.1) 
        
    print("\nAll stock data processing complete.")

if __name__ == "__main__":
    # Set this list to None to fetch all stocks
    # tickers_to_fetch = None 
    tickers_to_fetch = ["7203.T", "9984.T", "INVALID.T"] # Example with specific (and one invalid) tickers

    if tickers_to_fetch:
        print(f"--- Running fetch_stock_data.py for a specific list of {len(tickers_to_fetch)} tickers ---")
        main(specific_tickers=tickers_to_fetch)
    else:
        print("--- Running fetch_stock_data.py for all available JPX stock codes ---")
        main()
