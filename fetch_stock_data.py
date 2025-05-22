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

def fetch_and_save_stock_data(stock_code, target_csv_file_path):
    """
    Fetches historical stock data for a given stock code using yfinance
    and saves it to a single CSV file, performing differential updates.

    Args:
        stock_code (str): The stock code (e.g., "1301.T").
        target_csv_file_path (str): The path to the target CSV file.
    """
    start_date = None
    existing_data_df = None
    file_exists_and_not_empty = False

    if os.path.exists(target_csv_file_path) and os.path.getsize(target_csv_file_path) > 0:
        try:
            existing_data_df = pd.read_csv(target_csv_file_path)
            if not existing_data_df.empty and 'Date' in existing_data_df.columns and 'StockCode' in existing_data_df.columns:
                existing_data_df['Date'] = pd.to_datetime(existing_data_df['Date'])
                
                # Filter for the specific stock_code
                stock_specific_data = existing_data_df[existing_data_df['StockCode'] == stock_code]
                if not stock_specific_data.empty:
                    latest_date = stock_specific_data['Date'].max()
                    start_date = (latest_date + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
                    print(f"Existing data found for {stock_code}. Latest date: {latest_date.strftime('%Y-%m-%d')}. Fetching from {start_date}.")
                else:
                    print(f"No existing data found for {stock_code} in {target_csv_file_path}. Will fetch all history.")
                file_exists_and_not_empty = True # Indicates file has data, even if not for this specific stock
            else:
                print(f"File {target_csv_file_path} exists but is empty, missing 'Date' or 'StockCode' column. Will fetch all data for {stock_code} and overwrite/create.")
                file_exists_and_not_empty = False # Treat as if file is new/empty for writing purposes
        except Exception as e:
            print(f"Error reading existing file {target_csv_file_path}: {e}. Will attempt to fetch all data for {stock_code}.")
            file_exists_and_not_empty = False
    else:
        print(f"File {target_csv_file_path} does not exist or is empty. Will fetch all data for {stock_code}.")
        file_exists_and_not_empty = False

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
        new_data_df['Date'] = pd.to_datetime(new_data_df['Date'].dt.date) # Ensure only date part, no time
        new_data_df['StockCode'] = stock_code # Add StockCode column

    except Exception as e:
        print(f"Error fetching data from yfinance for {stock_code}: {e}")
        return

    try:
        if not new_data_df.empty:
            # Ensure consistent column order, placing StockCode typically after Date or at the end
            cols = ['Date', 'StockCode'] + [col for col in new_data_df.columns if col not in ['Date', 'StockCode']]
            new_data_df = new_data_df[cols]

            if file_exists_and_not_empty and start_date is not None and existing_data_df is not None:
                # Filter new_data_df to only include rows with a 'Date' greater than the latest_date for this stock_code
                # This check is crucial if yfinance returns overlapping data despite start_date
                stock_specific_data_in_file = existing_data_df[existing_data_df['StockCode'] == stock_code]
                if not stock_specific_data_in_file.empty:
                    latest_date_in_file_for_stock = stock_specific_data_in_file['Date'].max()
                    new_data_df = new_data_df[new_data_df['Date'] > latest_date_in_file_for_stock]
                
                if not new_data_df.empty:
                    new_data_df.to_csv(target_csv_file_path, mode='a', header=False, index=False)
                    print(f"Appended new data for {stock_code} to {target_csv_file_path}.")
                else:
                    print(f"No new data to append for {stock_code} after filtering (start_date: {start_date}).")
            else: # File does not exist, is empty, or no data for this stock code yet (so start_date was None)
                if file_exists_and_not_empty: # File exists but we are adding a new stock or overwriting
                    # If we are adding a new stock to an existing file, append without header
                    new_data_df.to_csv(target_csv_file_path, mode='a', header=False, index=False)
                    print(f"Appended new stock {stock_code} data to existing {target_csv_file_path}.")
                else:
                    # File is genuinely new or was empty, write with header
                    new_data_df.to_csv(target_csv_file_path, mode='w', header=True, index=False)
                    print(f"Saved initial data for {stock_code} to {target_csv_file_path}.")
    except Exception as e:
        print(f"Error saving data for {stock_code} to {target_csv_file_path}: {e}")

def main(test_codes=None, output_csv_path=None):
    """
    Main function to orchestrate fetching stock codes and their historical data.

    Args:
        test_codes (list, optional): A list of stock codes to process for testing.
                                     If None, fetches codes from JPX.
        output_csv_path (str, optional): Path to the output CSV file.
                                         If None, defaults to "stock_data/all_stocks_data.csv".
    """
    print("Starting the stock data fetching process...")

    if output_csv_path:
        target_csv = output_csv_path
    else:
        target_csv = os.path.join("stock_data", "all_stocks_data.csv")
    
    data_dir = os.path.dirname(target_csv)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory: {data_dir}")
        
    print(f"Target CSV file for all stock data: {target_csv}")

    stock_codes_to_process = []
    if test_codes is not None:
        print(f"Using provided test_codes: {test_codes}")
        stock_codes_to_process = test_codes
    else:
        print("Fetching stock codes from JPX...")
        stock_codes_to_process = get_stock_codes()
    
    if not stock_codes_to_process:
        print("No stock codes to process. Exiting.")
        return
        
    total_codes = len(stock_codes_to_process)
    print(f"Found {total_codes} stock codes to process.")

    for i, code in enumerate(stock_codes_to_process):
        print(f"\nProcessing stock {i+1} of {total_codes}: {code}")
        fetch_and_save_stock_data(code, target_csv_file_path=target_csv)
        # Optional: Add a small delay to avoid overwhelming the server
        # time.sleep(0.1) 
        
    print(f"\nAll stock data processing complete. Data saved to {target_csv}")

if __name__ == "__main__":
    main()
