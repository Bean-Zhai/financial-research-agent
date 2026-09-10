import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv


TICKERS = ["AAPL", "MSFT", "NVDA"]
START_DATE = "2022-01-01"
END_DATE = "2025-12-31"

SELECTED_COLUMNS = [
    "date",
    "open",
    "high",
    "low",
    "close",
    "adjClose",
    "volume"
]


def process_ticker(ticker, api_key):
    url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices"

    headers = {
        "Authorization": f"Token {api_key}"
    }

    params = {
        "startDate": START_DATE,
        "endDate": END_DATE
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()
    prices = pd.DataFrame(data)

    if prices.empty:
        raise ValueError(f"No price data was returned for {ticker}.")

    prices = prices[SELECTED_COLUMNS].copy()

    prices = prices.rename(
        columns={
            "adjClose": "adjusted_close"
        }
    )

    prices.insert(0, "ticker", ticker)

    prices["date"] = pd.to_datetime(
        prices["date"],
        utc=True
    )

    prices = prices.sort_values("date")
    prices = prices.reset_index(drop=True)

    missing_values = prices.isna().sum()
    duplicate_rows = prices.duplicated(
        subset=["ticker", "date"]
    ).sum()

    if missing_values.any():
        raise ValueError(
            f"Missing values were found for {ticker}:\n"
            f"{missing_values}"
        )

    if duplicate_rows > 0:
        raise ValueError(
            f"{duplicate_rows} duplicate rows were found for {ticker}."
        )

    project_root = Path(__file__).resolve().parents[2]
    output_directory = project_root / "data" / "processed"
    output_directory.mkdir(parents=True, exist_ok=True)

    start_year = START_DATE[:4]
    end_year = END_DATE[:4]

    output_file = (
        output_directory
        / f"{ticker}_prices_{start_year}_{end_year}.csv"
    )

    prices.to_csv(
        output_file,
        index=False,
        date_format="%Y-%m-%d"
    )

    print(f"\nCompleted: {ticker}")
    print(f"Rows: {len(prices)}")
    print(
        "Date range:",
        prices["date"].min(),
        "to",
        prices["date"].max()
    )
    print(f"Saved to: {output_file}")

    return prices


def main():
    load_dotenv()

    api_key = os.getenv("TIINGO_API_KEY")

    if not api_key:
        raise ValueError(
            "TIINGO_API_KEY was not found in the .env file."
        )

    for ticker in TICKERS:
        process_ticker(
            ticker=ticker,
            api_key=api_key
        )


if __name__ == "__main__":
    main()