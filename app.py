from flask import Flask, jsonify, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)

@app.route('/api/stock_data/<ticker>')
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        # 過去1年間のデータを取得
        hist = stock.history(period="1y")

        if hist.empty:
            return jsonify({"error": "Could not retrieve data for ticker"}), 404

        # 必要なデータを抽出して整形
        # 日付を YYYY-MM-DD 形式の文字列に変換
        hist.index = hist.index.strftime('%Y-%m-%d')

        # 終値だけを返す場合
        # return jsonify(hist['Close'].to_dict())

        # より詳細な情報を返す場合 (日付、始値, 高値, 安値, 終値, 出来高)
        chart_data = hist[['Open', 'High', 'Low', 'Close', 'Volume']].reset_index()
        # 'Date' カラム名を小文字に（JavaScript側で扱いやすくするため）
        chart_data.rename(columns={'Date': 'date', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)

        # 最新の株価情報も取得
        # info = stock.info # infoは多くの情報を取得するため、時間がかかる場合がある
        fast_info = stock.fast_info

        # 返却するデータ構造
        data = {
            "ticker": ticker,
            "chart_data": chart_data.to_dict(orient='records'),
            "current_price": fast_info.last_price if hasattr(fast_info, 'last_price') else None,
            "previous_close": fast_info.previous_close if hasattr(fast_info, 'previous_close') else None,
            "name": stock.info.get('shortName', stock.info.get('longName', ticker)) # 銘柄名 (取得に少し時間がかかるかも)
        }

        return jsonify(data)

    except Exception as e:
        app.logger.error(f"Error fetching data for {ticker}: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # デバッグモードで実行、ポート5001を使用 (フロントエンドとポートを分けるため)
    app.run(debug=True, port=5001)
