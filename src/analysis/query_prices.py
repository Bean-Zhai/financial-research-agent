import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "database" / "financial_data.db"


def main():
    with sqlite3.connect(DATABASE_PATH) as connection:
        summary_rows = connection.execute(
            """
            SELECT
                ticker,
                COUNT(*) AS row_count,
                MIN(date) AS start_date,
                MAX(date) AS end_date
            FROM daily_prices
            GROUP BY ticker
            ORDER BY ticker;
            """
        ).fetchall()

        latest_rows = connection.execute(
            """
            SELECT
                date,
                close,
                adjusted_close,
                volume
            FROM daily_prices
            WHERE ticker = ?
            ORDER BY date DESC
            LIMIT 5;
            """,
            ("AAPL",),
        ).fetchall()

    print("Database summary:")

    for ticker, row_count, start_date, end_date in summary_rows:
        print(
            f"{ticker}: {row_count} rows, "
            f"{start_date} to {end_date}"
        )

    print("\nLatest five AAPL trading days:")

    for date, close, adjusted_close, volume in latest_rows:
        print(
            f"{date} | close: {close:.2f} | "
            f"adjusted close: {adjusted_close:.2f} | "
            f"volume: {volume:,}"
        )


if __name__ == "__main__":
    main()