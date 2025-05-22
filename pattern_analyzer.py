"""
Analyzes stock data for patterns based on day of the week and week of the year.
"""

import pandas as pd

def analyze_day_of_week_patterns(df, buy_day_of_week, hold_trading_days):
    """
    Analyzes stock data to find patterns based on buying on a specific day of the
    week and holding for a certain number of trading days.

    Args:
        df (pd.DataFrame): DataFrame with 'Date', 'Close', 'DayOfWeek' columns.
        buy_day_of_week (int): Day of the week to simulate buying (0=Mon, ..., 6=Sun).
        hold_trading_days (int): Number of trading days to hold the stock.

    Returns:
        tuple: (probability, buy_signals_found)
               probability is successful_trades / buy_signals_found, or 0.
    """
    required_cols = ['Date', 'Close', 'DayOfWeek']
    for col in required_cols:
        if col not in df.columns:
            print(f"Error: DataFrame is missing required column: {col}")
            return (0, 0)

    # Filter out rows where 'Close' price is NaN or zero
    df_filtered = df.dropna(subset=['Close'])
    df_filtered = df_filtered[df_filtered['Close'] > 0]

    if df_filtered.empty:
        print("Warning: DataFrame is empty after filtering NaN/zero Close prices.")
        return (0, 0)

    buy_signals_found = 0
    successful_trades = 0

    # Iterate through the DataFrame. Using index is generally safer with pandas
    # especially when we need to look ahead for sell dates.
    for i in range(len(df_filtered)):
        current_row = df_filtered.iloc[i]

        if current_row['DayOfWeek'] == buy_day_of_week:
            buy_signals_found += 1
            buy_price = current_row['Close']

            # Determine sell index
            sell_index = i + hold_trading_days

            if sell_index < len(df_filtered):
                sell_price = df_filtered.iloc[sell_index]['Close']
                if sell_price > buy_price:
                    successful_trades += 1
            # else:
                # Not enough data to determine sell price for this buy signal

    if buy_signals_found == 0:
        return (0, 0)

    probability = successful_trades / buy_signals_found
    return (probability, buy_signals_found)

def analyze_quarterly_patterns(df, buy_quarter, hold_quarters):
    """
    Analyzes stock data for patterns based on buying in a specific quarter
    and holding for a certain number of quarters.

    Args:
        df (pd.DataFrame): DataFrame with 'Date', 'Close', 'Quarter', 'Year' columns.
        buy_quarter (int): Quarter to simulate buying (1, 2, 3, 4).
        hold_quarters (int): Number of quarters to hold the stock.

    Returns:
        tuple: (probability, buy_signals_found)
               probability is successful_trades / buy_signals_found, or 0.
    """
    required_cols = ['Date', 'Close', 'Quarter', 'Year']
    for col in required_cols:
        if col not in df.columns:
            print(f"Error: DataFrame is missing required column: {col}")
            return (0, 0)

    if not pd.api.types.is_datetime64_any_dtype(df['Date']):
        try:
            df['Date'] = pd.to_datetime(df['Date'])
        except Exception as e:
            print(f"Error converting 'Date' column to datetime: {e}")
            return (0, 0)

    df_filtered = df.dropna(subset=['Close'])
    df_filtered = df_filtered[df_filtered['Close'] > 0]

    if df_filtered.empty:
        print("Warning: DataFrame is empty after filtering NaN/zero Close prices.")
        return (0, 0)

    df_sorted = df_filtered.sort_values(by='Date')

    buy_signals_found = 0
    successful_trades = 0

    for year in df_sorted['Year'].unique():
        buy_quarter_data = df_sorted[
            (df_sorted['Year'] == year) & (df_sorted['Quarter'] == buy_quarter)
        ]

        if not buy_quarter_data.empty:
            buy_signals_found += 1
            buy_price = buy_quarter_data.iloc[0]['Close']
            buy_date = buy_quarter_data.iloc[0]['Date']

            # Determine target sell quarter and year using pd.Period
            buy_period = pd.Period(buy_date, freq='Q') # 'Q' for quarter-end frequency
            target_sell_period_start_date = (buy_period + hold_quarters).start_time.date()
            
            target_sell_year = target_sell_period_start_date.year
            # Convert target sell month to quarter
            target_sell_quarter = (target_sell_period_start_date.month - 1) // 3 + 1


            sell_quarter_data = df_sorted[
                (df_sorted['Year'] == target_sell_year) & (df_sorted['Quarter'] == target_sell_quarter)
            ]

            if not sell_quarter_data.empty:
                sell_price = sell_quarter_data.iloc[0]['Close']
                if sell_price > buy_price:
                    successful_trades += 1
            # else: Not enough data for this specific target sell quarter

    if buy_signals_found == 0:
        return (0, 0)

    probability = successful_trades / buy_signals_found
    return (probability, buy_signals_found)

def analyze_monthly_patterns(df, buy_month, hold_months):
    """
    Analyzes stock data for patterns based on buying in a specific month
    and holding for a certain number of months.

    Args:
        df (pd.DataFrame): DataFrame with 'Date', 'Close', 'Month', 'Year' columns.
        buy_month (int): Month to simulate buying (1=Jan, ..., 12=Dec).
        hold_months (int): Number of months to hold the stock.

    Returns:
        tuple: (probability, buy_signals_found)
               probability is successful_trades / buy_signals_found, or 0.
    """
    required_cols = ['Date', 'Close', 'Month', 'Year']
    for col in required_cols:
        if col not in df.columns:
            print(f"Error: DataFrame is missing required column: {col}")
            return (0, 0)

    if not pd.api.types.is_datetime64_any_dtype(df['Date']):
        try:
            df['Date'] = pd.to_datetime(df['Date'])
        except Exception as e:
            print(f"Error converting 'Date' column to datetime: {e}")
            return (0, 0)

    df_filtered = df.dropna(subset=['Close'])
    df_filtered = df_filtered[df_filtered['Close'] > 0]

    if df_filtered.empty:
        print("Warning: DataFrame is empty after filtering NaN/zero Close prices.")
        return (0, 0)

    df_sorted = df_filtered.sort_values(by='Date')

    buy_signals_found = 0
    successful_trades = 0

    for year in df_sorted['Year'].unique():
        buy_month_data = df_sorted[
            (df_sorted['Year'] == year) & (df_sorted['Month'] == buy_month)
        ]

        if not buy_month_data.empty:
            buy_signals_found += 1
            buy_price = buy_month_data.iloc[0]['Close']
            buy_date = buy_month_data.iloc[0]['Date']

            # Determine target sell month and year using pd.Period
            buy_period = pd.Period(buy_date, freq='M') # 'M' for month-end frequency
            target_sell_period_start_date = (buy_period + hold_months).start_time.date()
            
            target_sell_year = target_sell_period_start_date.year
            target_sell_month = target_sell_period_start_date.month

            sell_month_data = df_sorted[
                (df_sorted['Year'] == target_sell_year) & (df_sorted['Month'] == target_sell_month)
            ]

            if not sell_month_data.empty:
                sell_price = sell_month_data.iloc[0]['Close']
                if sell_price > buy_price:
                    successful_trades += 1
            # else: Not enough data for this specific target sell month

    if buy_signals_found == 0:
        return (0, 0)

    probability = successful_trades / buy_signals_found
    return (probability, buy_signals_found)

def analyze_weekly_patterns(df, buy_week_of_year, hold_weeks):
    """
    Analyzes stock data for patterns based on buying in a specific week of the
    year and holding for a certain number of weeks.

    Args:
        df (pd.DataFrame): DataFrame with 'Date', 'Close', 'WeekOfYear', 'Year' columns.
        buy_week_of_year (int): ISO week number to simulate buying.
        hold_weeks (int): Number of weeks to hold the stock.

    Returns:
        tuple: (probability, buy_signals_found)
               probability is successful_trades / buy_signals_found, or 0.
    """
    required_cols = ['Date', 'Close', 'WeekOfYear', 'Year']
    for col in required_cols:
        if col not in df.columns:
            print(f"Error: DataFrame is missing required column: {col}")
            return (0, 0)

    # Ensure 'Date' is datetime for sorting
    if not pd.api.types.is_datetime64_any_dtype(df['Date']):
        try:
            df['Date'] = pd.to_datetime(df['Date'])
        except Exception as e:
            print(f"Error converting 'Date' column to datetime: {e}")
            return (0, 0)

    # Filter out rows where 'Close' price is NaN or zero
    df_filtered = df.dropna(subset=['Close'])
    df_filtered = df_filtered[df_filtered['Close'] > 0]

    if df_filtered.empty:
        print("Warning: DataFrame is empty after filtering NaN/zero Close prices.")
        return (0, 0)

    # Sort by date to ensure correct identification of first trading day of a week
    df_sorted = df_filtered.sort_values(by='Date')

    buy_signals_found = 0
    successful_trades = 0

    # Iterate through each year present in the data
    for year in df_sorted['Year'].unique():
        # Find the first trading day of the buy_week_of_year in the current 'year'
        buy_week_data = df_sorted[
            (df_sorted['Year'] == year) & (df_sorted['WeekOfYear'] == buy_week_of_year)
        ]

        if not buy_week_data.empty:
            buy_signals_found += 1
            buy_price = buy_week_data.iloc[0]['Close'] # First trading day's close
            buy_date = buy_week_data.iloc[0]['Date']

            # Determine target sell year and week
            target_sell_year = year
            target_sell_week = buy_week_of_year + hold_weeks

            # Adjust for year overflow (ISO weeks can go up to 52 or 53)
            # This logic assumes a simple addition. A more robust solution would use
            # datetime arithmetic to add weeks and then extract the new year and week.
            # For simplicity, we'll use pandas' period arithmetic.
            
            # Start of the buy week
            buy_period = pd.Period(buy_date, freq='W')
            
            # Target sell period
            target_sell_period_start_date = (buy_period + hold_weeks).start_time.date()
            
            # Get the ISO year and week for the target sell date
            target_sell_year = target_sell_period_start_date.isocalendar()[0]
            target_sell_week = target_sell_period_start_date.isocalendar()[1]


            # Find the first trading day of the target_sell_week in target_sell_year
            sell_week_data = df_sorted[
                (df_sorted['Year'] == target_sell_year) & (df_sorted['WeekOfYear'] == target_sell_week)
            ]

            if not sell_week_data.empty:
                sell_price = sell_week_data.iloc[0]['Close'] # First trading day's close
                if sell_price > buy_price:
                    successful_trades += 1
            # else:
                # Not enough data for this specific target sell week

    if buy_signals_found == 0:
        return (0, 0)

    probability = successful_trades / buy_signals_found
    return (probability, buy_signals_found)
