import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "database" / "financial_data.db"


def main():
    with sqlite3.connect(DATABASE_PATH) as connection:
        prices = pd.read_sql_query(
            """
            SELECT
                ticker,
                date,
                adjusted_close
            FROM daily_prices
            ORDER BY ticker, date;
            """,
            connection,
            parse_dates=["date"],
        )

    prices["daily_return"] = (
        prices.groupby("ticker")["adjusted_close"]
        .pct_change()
    )

    print("Return analysis:\n")

    for ticker, ticker_data in prices.groupby("ticker"):
        daily_returns = ticker_data["daily_return"].dropna()

        start_price = ticker_data["adjusted_close"].iloc[0]
        end_price = ticker_data["adjusted_close"].iloc[-1]

        total_return = end_price / start_price - 1
        average_daily_return = daily_returns.mean()
        annualized_volatility = daily_returns.std() * np.sqrt(252)

        print(ticker)
        print(f"  Trading days: {len(ticker_data)}")
        print(f"  Start adjusted close: {start_price:.2f}")
        print(f"  End adjusted close: {end_price:.2f}")
        print(f"  Total return: {total_return:.2%}")
        print(
            f"  Average daily return: "
            f"{average_daily_return:.4%}"
        )
        print(
            f"  Annualized volatility: "
            f"{annualized_volatility:.2%}"
        )
        print()


if __name__ == "__main__":
    main()