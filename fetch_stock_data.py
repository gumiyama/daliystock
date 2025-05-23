import pandas as pd
import os
import yfinance as yf
import time  # Optional: to throttle requests

def get_stock_codes():
    """
    Fetches stock codes from the JPX website and formats them.
    """
    url = "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls"
    try:
        print("Fetching stock codes from JPX website...")
        df = pd.read_excel(url, skiprows=4, usecols=[1], header=None)
        raw = df.iloc[:,0]
        codes = []
        for v in raw:
            if pd.notna(v):
                try:
                    codes.append(f"{int(v)}.T")
                except:
                    pass
        print(f"Fetched {len(codes)} codes.")
        return codes
    except Exception as e:
        print(f"Error fetching stock codes: {e}")
        return []

def fetch_and_save_stock_data(stock_code, data_directory="stock_data"):
    """
    Fetches historical data for stock_code via yfinance,
    performs differential update, and saves to CSV.
    """
    # ディレクトリの作成
    if not os.path.exists(data_directory):
        try:
            os.makedirs(data_directory)
        except Exception as e:
            print(f"Error creating dir {data_directory}: {e}")
            return

    # CSV ファイルパスを 1 行で書く
    file_path = os.path.join(data_directory, f"{stock_code}.csv")

    # 既存ファイルの読み込みと差分開始日設定
    start_date = None
    existing_df = None
    if os.path.exists(file_path):
        try:
            existing_df = pd.read_csv(file_path, parse_dates=["Date"])
            if not existing_df.empty:
                latest = existing_df["Date"].max()
                start_date = (latest + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        except Exception as e:
            print(f"Error reading {file_path}: {e}. Fetching full history.")

    # yfinance からデータ取得
    try:
        ticker = yf.Ticker(stock_code)
        new_df = ticker.history(start=start_date, auto_adjust=True)
        if new_df.empty:
            print(f"No data for {stock_code} (start_date={start_date}).")
            return
        new_df.reset_index(inplace=True)
    except Exception as e:
        print(f"Error fetching {stock_code}: {e}")
        return

    # CSV への書き込み or 追記
    try:
        if existing_df is not None and start_date:
            to_append = new_df[new_df["Date"] > existing_df["Date"].max()]
            if not to_append.empty:
                to_append.to_csv(file_path, mode="a", header=False, index=False)
                print(f"Appended {len(to_append)} rows to {file_path}.")
            else:
                print(f"No new rows to append for {stock_code}.")
        else:
            new_df.to_csv(file_path, index=False)
            print(f"Saved full data for {stock_code} to {file_path}.")
    except Exception as e:
        print(f"Error saving {stock_code}: {e}")

def main(specific_tickers=None):
    """
    specific_tickers が None なら全コード取得、
    リスト指定ならそのリストのみ取得します。
    """
    if specific_tickers is None:
        tickers = get_stock_codes()
    else:
        tickers = specific_tickers

    print(f"Processing {len(tickers)} tickers…")
    for i, code in enumerate(tickers, start=1):
        print(f"[{i}/{len(tickers)}] {code}")
        fetch_and_save_stock_data(code)
        time.sleep(0.1)  # 必要に応じて調整
    print("Done.")

if __name__ == "__main__":
    # 全銘柄取得モード
    tickers_to_fetch = None

    if tickers_to_fetch:
        main(specific_tickers=tickers_to_fetch)
    else:
        print("=== 全銘柄を取得します ===")
        main()
