import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "database" / "financial_data.db"

TRADING_DAYS_PER_YEAR = 252
RISK_FREE_RATE = 0.0


def calculate_max_drawdown(daily_returns):
    investment_value = (1 + daily_returns).cumprod()
    previous_peak = investment_value.cummax()
    drawdown = investment_value / previous_peak - 1

    return drawdown.min()


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

    print("Risk-adjusted performance analysis:\n")

    for ticker, ticker_data in prices.groupby("ticker"):
        daily_returns = (
            ticker_data["adjusted_close"]
            .pct_change()
            .dropna()
        )

        daily_risk_free_rate = (
            (1 + RISK_FREE_RATE)
            ** (1 / TRADING_DAYS_PER_YEAR)
            - 1
        )

        annualized_volatility = (
            daily_returns.std()
            * np.sqrt(TRADING_DAYS_PER_YEAR)
        )

        sharpe_ratio = (
            (daily_returns.mean() - daily_risk_free_rate)
            / daily_returns.std()
            * np.sqrt(TRADING_DAYS_PER_YEAR)
        )

        maximum_drawdown = calculate_max_drawdown(
            daily_returns
        )

        print(ticker)
        print(
            f"  Annualized volatility: "
            f"{annualized_volatility:.2%}"
        )
        print(f"  Sharpe ratio: {sharpe_ratio:.2f}")
        print(
            f"  Maximum drawdown: "
            f"{maximum_drawdown:.2%}"
        )
        print()


if __name__ == "__main__":
    main()