PRAGMA foreign_keys = ON;


CREATE TABLE IF NOT EXISTS companies (
    ticker TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    sector TEXT,
    exchange TEXT,
    currency TEXT NOT NULL DEFAULT 'USD'
);


CREATE TABLE IF NOT EXISTS daily_prices (
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    adjusted_close REAL NOT NULL,
    volume INTEGER NOT NULL,

    PRIMARY KEY (ticker, date),

    FOREIGN KEY (ticker)
        REFERENCES companies(ticker)
);


CREATE INDEX IF NOT EXISTS idx_daily_prices_date
ON daily_prices(date);