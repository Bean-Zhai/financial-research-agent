import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "database" / "financial_data.db"

TRADING_DAYS_PER_YEAR = 252


def get_stock_metrics(ticker):
    ticker = ticker.strip().upper()

    with sqlite3.connect(DATABASE_PATH) as connection:
        prices = pd.read_sql_query(
            """
            SELECT
                date,
                adjusted_close
            FROM daily_prices
            WHERE ticker = ?
            ORDER BY date;
            """,
            connection,
            params=(ticker,),
            parse_dates=["date"],
        )

    if prices.empty:
        return {
            "success": False,
            "error": f"数据库中没有找到股票 {ticker}。",
        }

    daily_returns = (
        prices["adjusted_close"]
        .pct_change()
        .dropna()
    )

    start_price = prices["adjusted_close"].iloc[0]
    end_price = prices["adjusted_close"].iloc[-1]

    total_return = end_price / start_price - 1

    annualized_volatility = (
        daily_returns.std()
        * np.sqrt(TRADING_DAYS_PER_YEAR)
    )

    sharpe_ratio = (
        daily_returns.mean()
        / daily_returns.std()
        * np.sqrt(TRADING_DAYS_PER_YEAR)
    )

    investment_value = prices["adjusted_close"] / start_price
    previous_peak = investment_value.cummax()
    drawdown = investment_value / previous_peak - 1
    maximum_drawdown = drawdown.min()

    return {
        "success": True,
        "ticker": ticker,
        "start_date": prices["date"].iloc[0].strftime("%Y-%m-%d"),
        "end_date": prices["date"].iloc[-1].strftime("%Y-%m-%d"),
        "trading_days": len(prices),
        "start_price": round(float(start_price), 2),
        "end_price": round(float(end_price), 2),
        "total_return": round(float(total_return), 4),
        "annualized_volatility": round(
            float(annualized_volatility),
            4,
        ),
        "sharpe_ratio": round(float(sharpe_ratio), 2),
        "maximum_drawdown": round(
            float(maximum_drawdown),
            4,
        ),
    }

def get_latest_prices(ticker, limit=5):
    ticker = ticker.strip().upper()

    if limit <= 0:
        return {
            "success": False,
            "error": "查询天数必须大于0。",
        }

    with sqlite3.connect(DATABASE_PATH) as connection:
        latest_prices = pd.read_sql_query(
            """
            SELECT
                date,
                close,
                adjusted_close,
                volume
            FROM daily_prices
            WHERE ticker = ?
            ORDER BY date DESC
            LIMIT ?;
            """,
            connection,
            params=(ticker, limit),
        )

    if latest_prices.empty:
        return {
            "success": False,
            "error": f"数据库中没有找到股票 {ticker}。",
        }

    price_records = []

    for _, row in latest_prices.iterrows():
        price_records.append(
            {
                "date": row["date"],
                "close": round(float(row["close"]), 2),
                "adjusted_close": round(
                    float(row["adjusted_close"]),
                    2,
                ),
                "volume": int(row["volume"]),
            }
        )

    return {
        "success": True,
        "ticker": ticker,
        "number_of_records": len(price_records),
        "prices": price_records,
    }

def compare_stocks(tickers):
    stock_results = []

    for ticker in tickers:
        result = get_stock_metrics(ticker)

        if result["success"]:
            stock_results.append(result)

    if not stock_results:
        return {
            "success": False,
            "error": "没有找到可以比较的股票数据。",
        }

    highest_return = max(
        stock_results,
        key=lambda item: item["total_return"],
    )

    lowest_volatility = min(
        stock_results,
        key=lambda item: item["annualized_volatility"],
    )

    highest_sharpe = max(
        stock_results,
        key=lambda item: item["sharpe_ratio"],
    )

    smallest_drawdown = max(
        stock_results,
        key=lambda item: item["maximum_drawdown"],
    )

    return {
        "success": True,
        "stocks": stock_results,
        "comparison": {
            "highest_return": highest_return["ticker"],
            "lowest_volatility": lowest_volatility["ticker"],
            "highest_sharpe_ratio": highest_sharpe["ticker"],
            "smallest_maximum_drawdown": (
                smallest_drawdown["ticker"]
            ),
        },
    }

if __name__ == "__main__":
    print("1. Single-stock metrics:")
    print(get_stock_metrics("AAPL"))

    print("\n2. Latest prices:")
    print(get_latest_prices("MSFT", 3))

    print("\n3. Stock comparison:")
    print(compare_stocks(["AAPL", "MSFT", "NVDA"]))