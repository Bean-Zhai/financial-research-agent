import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv


load_dotenv()

api_key = os.getenv("TIINGO_API_KEY")

if not api_key:
    raise ValueError("TIINGO_API_KEY was not found in the .env file.")

url = "https://api.tiingo.com/tiingo/daily/AAPL/prices"

headers = {
    "Authorization": f"Token {api_key}"
}

params = {
    "startDate": "2022-01-01",
    "endDate": "2025-12-31"
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

selected_columns = [
    "date",
    "open",
    "high",
    "low",
    "close",
    "adjClose",
    "volume"
]

prices = prices[selected_columns].copy()

prices = prices.rename(
    columns={
        "adjClose": "adjusted_close"
    }
)

prices.insert(0, "ticker", "AAPL")

prices["date"] = pd.to_datetime(
    prices["date"],
    utc=True
)

prices = prices.sort_values("date")
prices = prices.reset_index(drop=True)

missing_values = prices.isna().sum()
duplicate_dates = prices.duplicated(
    subset=["ticker", "date"]
).sum()

print("HTTP status:", response.status_code)
print("Data shape:", prices.shape)
print("\nFirst five rows:")
print(prices.head().to_string(index=False))

print("\nColumn data types:")
print(prices.dtypes)

print("\nMissing values:")
print(missing_values)

print("\nDuplicate ticker-date rows:", duplicate_dates)
print(
    "Date range:",
    prices["date"].min(),
    "to",
    prices["date"].max()
)

project_root = Path(__file__).resolve().parents[2]

output_directory = project_root / "data" / "processed"
output_directory.mkdir(parents=True, exist_ok=True)

output_file = output_directory / "AAPL_prices_2022_2025.csv"

prices.to_csv(
    output_file,
    index=False,
    date_format="%Y-%m-%d"
)

print("\nData saved to:")
print(output_file)