"""
Main script to analyze stock data for buy signals on the next business day.

This script uses historical stock data and defined patterns to identify potential
buying opportunities. It considers patterns based on day of the week, week of the year,
month, and quarter.
"""

import os
import datetime
import data_utils
import pattern_analyzer
import market_utils

# Configuration
DATA_DIRECTORY = "stock_data"  # Directory containing stock CSV files
MIN_OCCURRENCES = 10  # Minimum number of pattern occurrences to consider a signal valid
MIN_PROBABILITY = 0.60  # Minimum probability of success to consider a signal strong
ANALYSIS_YEAR_START = 2010  # Start year for fetching holidays
ANALYSIS_YEAR_END = datetime.date.today().year + 1  # End year for fetching holidays (up to next year)

def get_stock_suggestions():
    """
    Core logic to find stock suggestions.
    1. Loads Japanese holidays.
    2. Determines the next business day and its properties.
    3. Lists available stock data files.
    4. Analyzes each stock for predefined patterns based on the next business day.
    Returns:
        tuple: (next_business_day_obj, all_strong_signals list)
               Returns (None, []) if critical errors occur (e.g., cannot determine next business day).
    """
    # a. Load Holidays
    print("Loading Japanese holidays...")
    jp_holidays = market_utils.get_japanese_holidays(ANALYSIS_YEAR_START, ANALYSIS_YEAR_END)
    if not jp_holidays:
        print("Warning: No holidays loaded. Business day calculations might be inaccurate.")
        # Consider if this is a critical error for the function's purpose
    
    # b. Determine Next Business Day
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    next_business_day_obj = market_utils.get_next_business_day(today_str, jp_holidays)

    if next_business_day_obj is None:
        print("Error: Could not determine the next business day.")
        return None, [] # Critical error, cannot proceed

    next_bday_dayofweek = next_business_day_obj.weekday()  # 0=Mon, 6=Sun
    next_bday_weekofyear = next_business_day_obj.isocalendar()[1]
    next_bday_month = next_business_day_obj.month
    next_bday_quarter = (next_business_day_obj.month - 1) // 3 + 1

    # These print statements are for CLI context, might be removed or conditional for library use
    print(f"\n--- Next Business Day Analysis for get_stock_suggestions ---")
    print(f"Today's Date: {today_str}")
    print(f"Calculated Next Business Day: {next_business_day_obj}")
    print(f"  Day of Week: {next_bday_dayofweek} (0=Mon, 1=Tue, ..., 6=Sun)")
    print(f"  ISO Week of Year: {next_bday_weekofyear}")
    print(f"  Month: {next_bday_month}")
    print(f"  Quarter: {next_bday_quarter}")
    print("-----------------------------------\n")

    # c. List Stock Files
    print(f"Looking for stock data in ./{DATA_DIRECTORY} ...")
    try:
        all_files = os.listdir(DATA_DIRECTORY)
        stock_files = [f for f in all_files if f.endswith('.csv')]
        if not stock_files:
            print(f"No CSV files found in {DATA_DIRECTORY}.")
            return next_business_day_obj, [] # Return with no signals if no files
        print(f"Found {len(stock_files)} stock CSV files.")
    except FileNotFoundError:
        print(f"Error: Data directory '{DATA_DIRECTORY}' not found.")
        # Raise an exception or return error state that GUI can catch
        raise # Reraise for GUI to handle
    except Exception as e:
        print(f"Error listing stock files in '{DATA_DIRECTORY}': {e}.")
        raise # Reraise for GUI to handle

    # d. Analyze Each Stock
    all_strong_signals = []
    print(f"\n--- Analyzing {len(stock_files)} Stock Files for get_stock_suggestions ---")

    for stock_file in stock_files:
        ticker = stock_file.replace(".csv", "")
        print(f"Analyzing {ticker} for get_stock_suggestions...")

        df = data_utils.load_stock_data(ticker, DATA_DIRECTORY)
        if df is None or df.empty:
            print(f"No data loaded for {ticker} in get_stock_suggestions. Skipping.")
            continue

        # Define patterns to test based on the next business day's properties
        # For all patterns, we are checking if buying on the next_business_day
        # (based on its dayofweek, weekofyear, month, quarter) is a good idea.

        # 1. Day of Week Pattern
        hold_days_options = [1, 2, 3, 4]
        for hold_duration in hold_days_options:
            prob_dow, occ_dow = pattern_analyzer.analyze_day_of_week_patterns(
                df,
                buy_day_of_week=next_bday_dayofweek,
                hold_trading_days=hold_duration
            )
            if occ_dow >= MIN_OCCURRENCES and prob_dow >= MIN_PROBABILITY:
                all_strong_signals.append({
                    "ticker": ticker,
                    "pattern": f"Buy on Day {next_bday_dayofweek}, Sell {hold_duration} trading day(s) later",
                    "prob": prob_dow, "occ": occ_dow # 'buy_on' is implicitly next_business_day_obj
                })

        # 2. Weekly Pattern
        hold_weeks_options = [1, 2]
        for hold_duration in hold_weeks_options:
            prob_w, occ_w = pattern_analyzer.analyze_weekly_patterns(
                df,
                buy_week_of_year=next_bday_weekofyear,
                hold_weeks=hold_duration
            )
            if occ_w >= MIN_OCCURRENCES and prob_w >= MIN_PROBABILITY:
                all_strong_signals.append({
                    "ticker": ticker,
                    "pattern": f"Buy Week {next_bday_weekofyear}, Sell {hold_duration} week(s) later",
                    "prob": prob_w, "occ": occ_w
                })

        # 3. Monthly Pattern
        prob_m, occ_m = pattern_analyzer.analyze_monthly_patterns(
            df,
            buy_month=next_bday_month,
            hold_months=1
        )
        if occ_m >= MIN_OCCURRENCES and prob_m >= MIN_PROBABILITY:
            all_strong_signals.append({
                "ticker": ticker,
                "pattern": f"Buy Month {next_bday_month}, Sell 1 month later",
                "prob": prob_m, "occ": occ_m
            })

        # 4. Quarterly Pattern
        prob_q, occ_q = pattern_analyzer.analyze_quarterly_patterns(
            df,
            buy_quarter=next_bday_quarter,
            hold_quarters=1
        )
        if occ_q >= MIN_OCCURRENCES and prob_q >= MIN_PROBABILITY:
            all_strong_signals.append({
                "ticker": ticker,
                "pattern": f"Buy Quarter {next_bday_quarter}, Sell 1 quarter later",
                "prob": prob_q, "occ": occ_q
            })
    
    return next_business_day_obj, all_strong_signals


def main():
    """
    Main function to orchestrate the stock analysis process and print results.
    Calls get_stock_suggestions() and displays the output.
    """
    try:
        next_bday_obj, signals = get_stock_suggestions()

        if next_bday_obj is None: # Indicates a critical error from get_stock_suggestions
            print("Exiting due to critical error in suggestion generation.")
            return

        print("\n--- CLI Results ---")
        if signals:
            print(f"--- Stock Suggestions for Next Business Day: {next_bday_obj} ---")
            # Sort by probability (descending), then by ticker for consistent ordering
            signals_sorted = sorted(signals, key=lambda x: (x['prob'], x['ticker']), reverse=True)
            
            for signal in signals_sorted:
                print(f"  Ticker: {signal['ticker']}, "
                      f"Pattern: {signal['pattern']}, "
                      f"Probability: {signal['prob']:.2f}, "
                      f"Occurrences: {signal['occ']}")
        else:
            print(f"No strong buy signals found for {next_bday_obj} based on current criteria.")

    except FileNotFoundError as e:
        print(f"Error: {e}. Please ensure the stock data directory exists and is populated.")
    except Exception as e:
        print(f"An unexpected error occurred in main: {e}")

    print("\nCLI Analysis complete.")


if __name__ == "__main__":
    main()
