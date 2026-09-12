import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "database" / "financial_data.db"
DATA_DIRECTORY = PROJECT_ROOT / "data" / "processed"

COMPANIES = [
    ("AAPL", "Apple Inc.", "Technology", "NASDAQ", "USD"),
    ("MSFT", "Microsoft Corporation", "Technology", "NASDAQ", "USD"),
    ("NVDA", "NVIDIA Corporation", "Technology", "NASDAQ", "USD"),
]


def load_companies(connection):
    connection.executemany(
        """
        INSERT INTO companies (
            ticker,
            company_name,
            sector,
            exchange,
            currency
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(ticker) DO UPDATE SET
            company_name = excluded.company_name,
            sector = excluded.sector,
            exchange = excluded.exchange,
            currency = excluded.currency;
        """,
        COMPANIES,
    )


def load_prices(connection):
    total_rows = 0

    for ticker, *_ in COMPANIES:
        csv_path = DATA_DIRECTORY / f"{ticker}_prices_2022_2025.csv"

        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        prices = pd.read_csv(csv_path)

        required_columns = [
            "ticker",
            "date",
            "open",
            "high",
            "low",
            "close",
            "adjusted_close",
            "volume",
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in prices.columns
        ]

        if missing_columns:
            raise ValueError(
                f"{ticker} is missing columns: {missing_columns}"
            )

        prices["date"] = (
            pd.to_datetime(prices["date"], utc=True)
            .dt.strftime("%Y-%m-%d")
        )

        rows = list(
            prices[required_columns].itertuples(
                index=False,
                name=None,
            )
        )

        connection.executemany(
            """
            INSERT INTO daily_prices (
                ticker,
                date,
                open,
                high,
                low,
                close,
                adjusted_close,
                volume
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ticker, date) DO UPDATE SET
                open = excluded.open,
                high = excluded.high,
                low = excluded.low,
                close = excluded.close,
                adjusted_close = excluded.adjusted_close,
                volume = excluded.volume;
            """,
            rows,
        )

        total_rows += len(rows)
        print(f"Loaded {ticker}: {len(rows)} rows")

    return total_rows


def main():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")

        load_companies(connection)
        total_loaded = load_prices(connection)

        company_count = connection.execute(
            "SELECT COUNT(*) FROM companies;"
        ).fetchone()[0]

        price_count = connection.execute(
            "SELECT COUNT(*) FROM daily_prices;"
        ).fetchone()[0]

        ticker_counts = connection.execute(
            """
            SELECT ticker, COUNT(*)
            FROM daily_prices
            GROUP BY ticker
            ORDER BY ticker;
            """
        ).fetchall()

    print("\nDatabase loading completed.")
    print(f"Rows processed this time: {total_loaded}")
    print(f"Companies in database: {company_count}")
    print(f"Price rows in database: {price_count}")
    print(f"Rows by ticker: {ticker_counts}")


if __name__ == "__main__":
    main()