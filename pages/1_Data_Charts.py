import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATABASE_PATH = (
    PROJECT_ROOT / "database" / "financial_data.db"
)

TRADING_DAYS_PER_YEAR = 252


st.set_page_config(
    page_title="数据图表",
    page_icon="📈",
    layout="wide",
)


def load_database_summary():
    with sqlite3.connect(DATABASE_PATH) as connection:
        return pd.read_sql_query(
            """
            SELECT
                ticker,
                MIN(date) AS start_date,
                MAX(date) AS end_date
            FROM daily_prices
            GROUP BY ticker
            ORDER BY ticker;
            """,
            connection,
        )


def load_prices(
    tickers,
    start_date,
    end_date,
):
    placeholders = ",".join(
        "?" for _ in tickers
    )

    query = f"""
        SELECT
            ticker,
            date,
            adjusted_close
        FROM daily_prices
        WHERE ticker IN ({placeholders})
          AND date >= ?
          AND date <= ?
        ORDER BY date;
    """

    parameters = (
        list(tickers)
        + [start_date, end_date]
    )

    with sqlite3.connect(DATABASE_PATH) as connection:
        return pd.read_sql_query(
            query,
            connection,
            params=parameters,
            parse_dates=["date"],
        )


st.title("📈 交互式金融数据图表")

st.caption(
    "选择股票和日期范围，查看历史表现、"
    "收益风险指标、相关性与滚动波动率。"
)


database_summary = load_database_summary()

available_tickers = (
    database_summary["ticker"].tolist()
)

minimum_date = pd.to_datetime(
    database_summary["start_date"].min()
).date()

maximum_date = pd.to_datetime(
    database_summary["end_date"].max()
).date()


with st.sidebar:
    st.header("图表设置")

    selected_tickers = st.multiselect(
        "选择股票",
        options=available_tickers,
        default=available_tickers,
    )

    selected_dates = st.date_input(
        "选择分析区间",
        value=(minimum_date, maximum_date),
        min_value=minimum_date,
        max_value=maximum_date,
    )

    rolling_window = st.slider(
        "滚动波动率窗口",
        min_value=10,
        max_value=120,
        value=20,
        step=5,
    )


if not selected_tickers:
    st.warning("请至少选择一只股票。")
    st.stop()


if len(selected_dates) != 2:
    st.info("请选择开始日期和结束日期。")
    st.stop()


start_date = selected_dates[0].isoformat()
end_date = selected_dates[1].isoformat()


prices = load_prices(
    tickers=selected_tickers,
    start_date=start_date,
    end_date=end_date,
)


if prices.empty:
    st.warning("指定区间内没有可用数据。")
    st.stop()


price_table = prices.pivot(
    index="date",
    columns="ticker",
    values="adjusted_close",
)


st.subheader("收益与风险概览")

summary_rows = []

for ticker in price_table.columns:
    ticker_prices = price_table[ticker].dropna()

    daily_returns = (
        ticker_prices
        .pct_change()
        .dropna()
    )

    total_return = (
        ticker_prices.iloc[-1]
        / ticker_prices.iloc[0]
        - 1
    )

    annualized_volatility = (
        daily_returns.std()
        * np.sqrt(TRADING_DAYS_PER_YEAR)
    )

    investment_value = (
        ticker_prices / ticker_prices.iloc[0]
    )

    drawdown = (
        investment_value
        / investment_value.cummax()
        - 1
    )

    summary_rows.append(
        {
            "股票": ticker,
            "累计收益率": total_return,
            "年化波动率": annualized_volatility,
            "最大回撤": drawdown.min(),
        }
    )


summary_table = pd.DataFrame(summary_rows)

st.dataframe(
    summary_table.style.format(
        {
            "累计收益率": "{:.2%}",
            "年化波动率": "{:.2%}",
            "最大回撤": "{:.2%}",
        }
    ),
    use_container_width=True,
    hide_index=True,
)


st.subheader("100美元投资价值变化")

normalized_performance = price_table.copy()

for ticker in normalized_performance.columns:
    first_price = (
        normalized_performance[ticker]
        .dropna()
        .iloc[0]
    )

    normalized_performance[ticker] = (
        normalized_performance[ticker]
        / first_price
        * 100
    )

st.line_chart(
    normalized_performance,
    y_label="投资价值（美元）",
)


daily_returns = price_table.pct_change(
    fill_method=None
)


if len(price_table.columns) >= 2:
    st.subheader("每日收益率相关性")

    correlation_matrix = daily_returns.corr()

    st.dataframe(
        correlation_matrix.style.format("{:.2f}"),
        use_container_width=True,
    )


st.subheader(
    f"{rolling_window}日滚动年化波动率"
)

rolling_volatility = (
    daily_returns
    .rolling(window=rolling_window)
    .std()
    * np.sqrt(TRADING_DAYS_PER_YEAR)
)

st.line_chart(
    rolling_volatility.dropna(how="all"),
    y_label="年化波动率",
)


st.caption(
    "以上结果基于历史调整后收盘价计算，"
    "仅供数据研究使用，不构成投资建议。"
)