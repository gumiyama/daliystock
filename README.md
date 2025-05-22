# Stock Pattern Suggester

## Overview
This project analyzes historical stock data for publicly traded companies on the Japanese stock market (JPX) to identify time-based patterns. It aims to suggest potential buying opportunities for the next business day based on these historical trends. The suggestions are presented through a simple Graphical User Interface (GUI).

## Features
*   Fetches and updates historical stock data for JPX-listed companies (from Yahoo Finance via `yfinance`).
*   Identifies potential buying patterns based on:
    *   **Day of the week:** e.g., buy on Monday, sell N trading days later.
    *   **Week of the year:** e.g., buy in week X, sell Y weeks later.
    *   **Month of the year:** e.g., buy in month M, sell N months later.
    *   **Quarter of the year:** e.g., buy in quarter Q, sell P quarters later.
*   Provides a GUI (`stock_suggester_gui.py`) to display actionable suggestions for the next calculated business day.
*   Includes command-line interfaces for data fetching (`fetch_stock_data.py`) and analysis (`main_analyzer.py`).
*   Handles Japanese holidays to accurately determine business days.
*   Unit tests for core logic modules (`market_utils.py`, `pattern_analyzer.py`).

## Project Structure
*   `fetch_stock_data.py`: Script to download historical stock data for JPX-listed companies. Can fetch all or specific tickers. Performs differential updates.
*   `data_utils.py`: Utility functions to load and preprocess stock data from CSV files, including adding time-based features.
*   `market_utils.py`: Handles market-specific logic, primarily for determining Japanese holidays and calculating the next business day.
*   `pattern_analyzer.py`: Contains the core logic for analyzing historical data to find day-of-week, weekly, monthly, and quarterly patterns.
*   `main_analyzer.py`: Orchestrates the analysis by using the other utility and analyzer modules. It provides suggestions via a command-line interface and is also used by the GUI.
*   `stock_suggester_gui.py`: The Tkinter-based GUI application that presents stock suggestions.
*   `tests/`: Directory containing unit tests.
    *   `test_market_utils.py`: Tests for holiday and business day calculations.
    *   `test_pattern_analyzer.py`: Tests for the pattern analysis functions.
*   `stock_data/`: Default directory where downloaded CSV stock data files are stored. Each file is named `{TickerSymbol}.csv`.
*   `.gitignore`: Specifies intentionally untracked files that Git should ignore.
*   `README.md`: This file.

## Setup & Installation
1.  **Python:** Ensure you have Python 3.x installed (developed with Python 3.10+).
2.  **Libraries:** Install the required Python libraries. A `requirements.txt` file is not yet provided, but you can install them using pip:
    ```bash
    pip install pandas yfinance holidays jpx_data_utils # jpx_data_utils is for an alternative get_stock_codes
    ```
    *   `pandas`: For data manipulation and analysis.
    *   `yfinance`: To download historical stock market data from Yahoo Finance.
    *   `holidays`: To determine Japanese holidays for accurate business day calculations.
    *   `jpx_data_utils`: (Used in some versions of `fetch_stock_data.py` for fetching the list of JPX stock codes; the current version might use direct pandas reading from an Excel file from JPX).

## How to Run

### 1. Fetching Stock Data
This step is crucial as the analysis relies on locally stored data.
*   **To fetch/update data for all JPX listed stocks:**
    Open a terminal or command prompt, navigate to the project's root directory, and run:
    ```bash
    python fetch_stock_data.py
    ```
    The script will attempt to download data for all companies. If run previously, it will perform a differential update for each stock based on the last fetched date (logged in `last_fetch_log.json` if that version of script is used, otherwise it checks data in CSVs).
*   **To fetch/update data for specific tickers:**
    You can modify the `fetch_stock_data.py` script. Near the end, in the `if __name__ == "__main__":` block, you can provide a list of tickers:
    ```python
    # Example:
    tickers_to_fetch = ["7203.T", "9984.T"] # Toyota and SoftBank
    main(specific_tickers=tickers_to_fetch)
    ```
    If `tickers_to_fetch` is `None`, it will fetch all stocks.

*   **Data Storage:** Stock data is saved as CSV files in the `stock_data/` directory.

### 2. Running the GUI Application
To view stock suggestions through the GUI:
```bash
python stock_suggester_gui.py
```
The GUI will load, and you can click the "Find Stock Suggestions for Next Business Day" button. It uses the data previously fetched into the `stock_data/` directory. Results will appear in the text area.

### 3. Running the Command-Line Analyzer
For a command-line version of the suggestions:
```bash
python main_analyzer.py
```
This script will print the analysis and suggestions directly to the console.

### 4. Running Tests
To ensure the core logic is working as expected:
```bash
python -m unittest discover tests
```
This command will automatically find and run all tests within the `tests/` directory.

## Interpreting Results
The suggestions provided by the GUI or command-line analyzer will typically look like this:

`Ticker: 7203.T, Pattern: Buy on Day 0 (Mon), Sell 4 trading day(s) later, Probability: 0.68, Occurrences: 25`

*   **Ticker:** The stock symbol (e.g., `7203.T` for Toyota Motor Corp.).
*   **Pattern:** The historical pattern identified.
    *   "Buy on Day 0 (Mon), Sell 4 trading day(s) later" means the pattern is to buy on Monday and sell 4 trading days after that (which would typically be Friday if there are no intervening holidays).
    *   Other patterns will specify buy week/month/quarter and holding period.
*   **Probability:** The historical probability of this pattern resulting in a profitable trade (i.e., sell price > buy price). A probability of 0.68 means it was profitable 68% of the time.
*   **Occurrences:** The number of times this specific pattern was observed in the historical data for that stock.

**Disclaimer:**
**This tool is for informational and educational purposes only and does NOT constitute financial advice. Stock market investments are subject to market risks. Past performance is not indicative of future results. Always conduct your own thorough research or consult with a qualified financial advisor before making any investment decisions.**

## Future Improvements
*   **Backtesting Framework:** Implement a more robust backtesting system to evaluate the historical performance of identified patterns with simulated trades, including profit/loss calculation.
*   **More Sophisticated Pattern Definitions:** Allow for more complex patterns, potentially incorporating volume data, moving averages, or other technical indicators.
*   **Configuration File:** Move parameters like `MIN_OCCURRENCES`, `MIN_PROBABILITY`, date ranges, and data directory paths into a configuration file (e.g., JSON or YAML) for easier modification.
*   **Error Logging:** Implement more comprehensive logging to a file, especially for the data fetching process, to better track errors and API issues.
*   **Improved GUI:** Enhance the GUI with more features like filtering, sorting, plotting historical data for selected stocks, and managing analysis parameters.
*   **`requirements.txt`:** Generate a `requirements.txt` file for easier dependency management.
*   **Async Operations:** For the GUI, make the analysis step asynchronous to prevent the UI from freezing during potentially long calculations.
