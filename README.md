# Stock Data Fetcher for TSE

This script fetches daily historical stock price data for all tickers listed on the Tokyo Stock Exchange (TSE) and saves it into individual CSV files. It performs differential updates, meaning it only fetches new data since the last recorded date for each stock.

## Prerequisites

*   Python 3.x
*   The script uses the following Python libraries:
    *   `pandas`
    *   `yfinance`
    *   `openpyxl` (required by pandas to read Excel files)

## Setup

1.  **Clone the repository (if applicable) or download the `fetch_stock_data.py` script.**

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install pandas yfinance openpyxl
    ```
    Alternatively, you can create a `requirements.txt` file with the following content:
    ```
    pandas
    yfinance
    openpyxl
    ```
    And then install using:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the script:**
    ```bash
    python fetch_stock_data.py
    ```

2.  **Output:**
    *   The script will create a directory named `stock_data/` in the same directory where the script is run.
    *   Inside `stock_data/`, individual CSV files for each stock ticker (e.g., `1301.T.csv`) will be created or updated.
    *   The script will print progress messages to the console, including any errors encountered.

## How it Works

1.  **Fetches Stock Codes:** Downloads an Excel file from the Japan Exchange Group (JPX) website containing a list of TSE tickers.
2.  **Processes Codes:** Extracts the ticker symbols and formats them (e.g., appends ".T") for compatibility with the `yfinance` library.
3.  **Fetches Historical Data:** For each ticker:
    *   Checks if a CSV file already exists in `stock_data/`.
    *   If yes, it determines the last date for which data was saved and fetches only new data from `yfinance` since that date.
    *   If no, it fetches all available historical data from `yfinance`.
    *   Saves the data to `<ticker>.csv` in the `stock_data/` directory. New data is appended to existing files.

## Error Handling
The script includes basic error handling for:
*   Network issues when downloading the JPX Excel file.
*   Errors during `yfinance` data fetching (e.g., invalid tickers, temporary API issues).
*   File I/O operations.

Errors are printed to the console.
