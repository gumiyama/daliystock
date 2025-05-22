# Script for analyzing stock seasonality
import pandas as pd
from datetime import datetime, timedelta

def load_and_preprocess_data(csv_path):
    """
    Loads data from a CSV file and preprocesses it.

    Args:
        csv_path (str): The path to the CSV file.

    Returns:
        pandas.DataFrame: The processed DataFrame, or None if loading/preprocessing fails.
    """
    try:
        df = pd.read_csv(csv_path)
        print(f"Successfully loaded data from {csv_path}.")
    except FileNotFoundError:
        print(f"Error: The file {csv_path} was not found.")
        return None
    except Exception as e:
        print(f"An error occurred while reading {csv_path}: {e}")
        return None

    if 'Date' not in df.columns:
        print("Error: 'Date' column not found in the CSV file.")
        return None
        
    try:
        # Ensure 'Date' is interpreted correctly, handling potential errors
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        if df['Date'].isnull().any():
            print("Warning: Some 'Date' values could not be parsed and were set to NaT.")
            # Optionally, drop rows where Date is NaT if critical for further analysis
            # df.dropna(subset=['Date'], inplace=True)
    except Exception as e:
        print(f"Error converting 'Date' column to datetime: {e}")
        return None

    # Extract date components
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df['Quarter'] = (df['Month'] - 1) // 3 + 1
    df['DayOfWeek'] = df['Date'].dt.dayofweek  # Monday=0, Sunday=6

    print("Data preprocessing complete. Added 'Year', 'Month', 'Quarter', 'DayOfWeek' columns.")
    return df

def main():
    """
    Main function to orchestrate the seasonality analysis.
    """
    print("Seasonality analysis script started.")
    
    csv_file_path = "stock_data/all_stocks_data.csv"
    df = load_and_preprocess_data(csv_file_path)

    if df is not None and not df.empty:
        print(f"Data loaded and preprocessed successfully. Shape: {df.shape}")
        print("First 5 rows of the DataFrame:")
        print(df.head())
    else:
        print("Data loading and preprocessing failed or returned an empty DataFrame.")
        
    # Future analysis functions will be called here
    quarterly_summary_df = analyze_quarterly_seasonality(df)

    if quarterly_summary_df is not None and not quarterly_summary_df.empty:
        print("\nQuarterly Seasonality Analysis Summary:")
        print(quarterly_summary_df)
    else:
        print("\nQuarterly seasonality analysis did not return any results or failed.")

    suggest_trades_for_next_business_day(quarterly_summary_df)

    print("Seasonality analysis script finished.")

def suggest_trades_for_next_business_day(seasonality_summary_df):
    """
    Suggests potential trades for the next business day based on seasonality analysis,
    if the next business day is near the start of a quarter.

    Args:
        seasonality_summary_df (pandas.DataFrame): DataFrame with 'StockCode', 
                                                 'PatternType', 'AverageProfitability'.
    """
    if seasonality_summary_df is None or seasonality_summary_df.empty:
        print("\nNo seasonality summary data available to suggest trades.")
        return

    current_date = datetime.today().date()
    next_day = current_date + timedelta(days=1)

    # Adjust for weekends
    if next_day.weekday() == 5:  # Saturday
        next_business_day = next_day + timedelta(days=2)
    elif next_day.weekday() == 6:  # Sunday
        next_business_day = next_day + timedelta(days=1)
    else:
        next_business_day = next_day
    
    print(f"\nCalculating trade suggestions for next business day: {next_business_day.strftime('%Y-%m-%d')}")

    next_bday_year = next_business_day.year
    next_bday_month = next_business_day.month
    next_bday_day = next_business_day.day
    next_bday_quarter = (next_bday_month - 1) // 3 + 1

    # Heuristic: Check if next business day is within the first 7 days of a quarter-starting month
    is_start_of_quarter_period = next_bday_month in [1, 4, 7, 10] and next_bday_day <= 7

    if is_start_of_quarter_period:
        print(f"Next business day {next_business_day.strftime('%Y-%m-%d')} is potentially the start of Q{next_bday_quarter}.")
        
        target_quarter = next_bday_quarter
        
        # Pattern 1: Buy at start of target_quarter, sell at end of target_quarter
        pattern_same_q = f"Q{target_quarter}_Same"
        suggestions_same_q = seasonality_summary_df[
            (seasonality_summary_df['PatternType'] == pattern_same_q) &
            (seasonality_summary_df['AverageProfitability'] > 0)
        ]

        # Pattern 2: Buy at start of previous_quarter, sell at end of target_quarter
        # This interpretation is slightly off from "Buy at start of target_quarter based on previous trends"
        # The patterns Q{prev}_to_Q{target} actually mean "Buy start of Q{prev}, sell end of Q{target}"
        # For suggesting a buy at start of Q{target}, we should look for patterns that *enter* in Q{target}.
        # The prompt says: "filter for patterns like Q{target_quarter-1}_to_Q{target_quarter}"
        # This means we are looking for an entry in previous_quarter that has historically been profitable
        # when held until the end of the current target_quarter.
        # This specific pattern type is not what we want if we are to *enter* at target_quarter.
        #
        # Let's re-evaluate. The patterns are:
        # QX_Same: Enter start of QX, exit end of QX.
        # QX_to_QY: Enter start of QX, exit end of QY.
        #
        # If next_business_day is start of Q{target_quarter}, we are looking for patterns that suggest
        # entering *now* (i.e. start of Q{target_quarter}).
        # So, Q{target_quarter}_Same is relevant.
        # And Q{target_quarter}_to_Q{target_quarter+1} is also relevant (buy start of target, sell end of next).
        #
        # The request: "Also, filter for patterns like Q{target_quarter-1}_to_Q{target_quarter}"
        # This implies we should look for stocks that, if one had bought them at the start of
        # *previous* quarter, would be profitable by end of *current* quarter. This is not an entry signal for *today*.
        #
        # Sticking to the exact request:
        previous_quarter_for_pattern = target_quarter - 1
        if target_quarter == 1:
            previous_quarter_for_pattern = 4 # Q4 of the previous year, pattern implies entry year.
        
        pattern_prev_to_target_q = f"Q{previous_quarter_for_pattern}_to_Q{target_quarter}"
        suggestions_prev_to_target_q = seasonality_summary_df[
            (seasonality_summary_df['PatternType'] == pattern_prev_to_target_q) &
            (seasonality_summary_df['AverageProfitability'] > 0)
        ]
        
        suggested_stock_codes = set()
        if not suggestions_same_q.empty:
            suggested_stock_codes.update(suggestions_same_q['StockCode'].tolist())
            print(f"\nBased on '{pattern_same_q}' (buy start Q{target_quarter}, sell end Q{target_quarter}) with positive avg. profitability:")
            for stock in suggestions_same_q['StockCode'].unique():
                print(f"- {stock} (Avg. Profitability: {suggestions_same_q[suggestions_same_q['StockCode'] == stock]['AverageProfitability'].iloc[0]:.2%})")


        if not suggestions_prev_to_target_q.empty:
            suggested_stock_codes.update(suggestions_prev_to_target_q['StockCode'].tolist())
            print(f"\nBased on '{pattern_prev_to_target_q}' (buy start Q{previous_quarter_for_pattern}, sell end Q{target_quarter}) with positive avg. profitability:")
            print("(Note: This pattern implies an entry at the start of the *previous* quarter.)")
            for stock in suggestions_prev_to_target_q['StockCode'].unique():
                 print(f"- {stock} (Avg. Profitability: {suggestions_prev_to_target_q[suggestions_prev_to_target_q['StockCode'] == stock]['AverageProfitability'].iloc[0]:.2%})")
        
        if not suggested_stock_codes:
            print("No specific stock suggestions based on positive profitability for quarterly patterns starting this period.")
        else:
            # This part might be redundant if individual print statements above are preferred.
            # print("\nCombined unique suggested stock codes for consideration (entry at start of Q{target_quarter}):")
            # for stock_code in sorted(list(suggested_stock_codes)): # Filtered by patterns relevant to Q-target start
            #    print(f"- {stock_code}")
            pass

    else:
        print(f"Next business day {next_business_day.strftime('%Y-%m-%d')} is not considered the start of a quarter (Q{next_bday_quarter}). No quarterly-entry suggestions based on this heuristic.")


def analyze_quarterly_seasonality(df):
    """
    Analyzes quarterly stock seasonality based on entry and exit prices.

    Args:
        df (pandas.DataFrame): Preprocessed DataFrame with stock data.
                               Must include 'StockCode', 'Year', 'Quarter', 
                               'Date', 'Open', 'Close'.

    Returns:
        pandas.DataFrame: A summary DataFrame with 'StockCode', 'PatternType', 
                          and 'AverageProfitability', or None if analysis fails.
    """
    if df is None or df.empty:
        print("Error: Input DataFrame is None or empty for quarterly analysis.")
        return None

    required_columns = ['StockCode', 'Year', 'Quarter', 'Date', 'Open', 'Close']
    if not all(col in df.columns for col in required_columns):
        print(f"Error: Missing one or more required columns for quarterly analysis. Need: {required_columns}")
        return None

    results_list = []

    unique_stock_codes = df['StockCode'].unique()
    unique_years = sorted(df['Year'].unique()) # Ensure years are processed in order

    for stock_code in unique_stock_codes:
        stock_data = df[df['StockCode'] == stock_code].copy()
        # Sort by date to ensure correct first/last trading day selection
        stock_data.sort_values(by='Date', inplace=True)

        for year in unique_years:
            for quarter in range(1, 5):  # Q1, Q2, Q3, Q4
                # --- Same-Quarter Profitability ---
                current_quarter_data = stock_data[
                    (stock_data['Year'] == year) & (stock_data['Quarter'] == quarter)
                ]

                if not current_quarter_data.empty:
                    entry_price_row = current_quarter_data.iloc[0]
                    exit_price_row = current_quarter_data.iloc[-1]
                    
                    entry_price = entry_price_row['Open']
                    exit_price_same_q = exit_price_row['Close']

                    if pd.notna(entry_price) and pd.notna(exit_price_same_q) and entry_price != 0:
                        profitability = (exit_price_same_q - entry_price) / entry_price
                        results_list.append({
                            'StockCode': stock_code,
                            'Year': year,
                            'EntryQuarter': quarter,
                            'PatternType': f"Q{quarter}_Same",
                            'Profitability': profitability
                        })

                # --- Next-Quarter Profitability ---
                # Entry price is the same as for Same-Quarter
                if not current_quarter_data.empty: # Need current quarter data for entry price
                    entry_price_row_for_next_q = current_quarter_data.iloc[0]
                    entry_price_next_q_pattern = entry_price_row_for_next_q['Open']

                    if pd.notna(entry_price_next_q_pattern) and entry_price_next_q_pattern != 0:
                        exit_year_next_q = year
                        exit_quarter_next_q = quarter + 1
                        if quarter == 4:
                            exit_quarter_next_q = 1
                            exit_year_next_q = year + 1
                        
                        next_quarter_data = stock_data[
                            (stock_data['Year'] == exit_year_next_q) & 
                            (stock_data['Quarter'] == exit_quarter_next_q)
                        ]

                        if not next_quarter_data.empty:
                            exit_price_row_next_q = next_quarter_data.iloc[-1]
                            exit_price_next_q = exit_price_row_next_q['Close']

                            if pd.notna(exit_price_next_q):
                                profitability_next_q = (exit_price_next_q - entry_price_next_q_pattern) / entry_price_next_q_pattern
                                results_list.append({
                                    'StockCode': stock_code,
                                    'Year': year, # Year of entry
                                    'EntryQuarter': quarter, # Quarter of entry
                                    'PatternType': f"Q{quarter}_to_Q{exit_quarter_next_q}",
                                    'Profitability': profitability_next_q
                                })
    
    if not results_list:
        print("No profitability records were generated. Check data availability and ranges.")
        return None

    summary_df = pd.DataFrame(results_list)
    
    # Calculate average profitability for each pattern type per stock
    # We group by StockCode and the constructed PatternType
    average_profitability_df = summary_df.groupby(['StockCode', 'PatternType'])['Profitability'].mean().reset_index()
    average_profitability_df.rename(columns={'Profitability': 'AverageProfitability'}, inplace=True)
    
    print("Quarterly seasonality analysis complete.")
    return average_profitability_df

if __name__ == "__main__":
    main()
