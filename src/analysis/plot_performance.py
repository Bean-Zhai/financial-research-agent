import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "database" / "financial_data.db"

OUTPUT_DIRECTORY = PROJECT_ROOT / "reports" / "figures"
OUTPUT_PATH = OUTPUT_DIRECTORY / "stock_performance.png"


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

    prices["investment_value"] = (
        prices.groupby("ticker")["adjusted_close"]
        .transform(lambda prices: prices / prices.iloc[0] * 100)
    )

    performance = prices.pivot(
        index="date",
        columns="ticker",
        values="investment_value",
    )

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    ax = performance.plot(figsize=(11, 6), linewidth=2)

    ax.axhline(
        y=100,
        color="gray",
        linestyle="--",
        linewidth=1,
    )

    ax.set_title("Growth of a $100 Investment")
    ax.set_xlabel("Date")
    ax.set_ylabel("Investment Value ($)")
    ax.grid(alpha=0.3)
    ax.legend(title="Ticker")

    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=300)
    print(f"Chart saved to: {OUTPUT_PATH}")



if __name__ == "__main__":
    main()