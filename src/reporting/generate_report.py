import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "database" / "financial_data.db"
REPORT_PATH = PROJECT_ROOT / "reports" / "stock_analysis_report.md"

TRADING_DAYS_PER_YEAR = 252


def calculate_metrics(prices):
    results = []

    for ticker, ticker_data in prices.groupby("ticker"):
        ticker_data = ticker_data.sort_values("date")

        daily_returns = (
            ticker_data["adjusted_close"]
            .pct_change()
            .dropna()
        )

        start_price = ticker_data["adjusted_close"].iloc[0]
        end_price = ticker_data["adjusted_close"].iloc[-1]

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

        investment_value = (
            ticker_data["adjusted_close"] / start_price
        )

        previous_peak = investment_value.cummax()

        drawdown = investment_value / previous_peak - 1
        maximum_drawdown = drawdown.min()

        results.append(
            {
                "ticker": ticker,
                "total_return": total_return,
                "annualized_volatility": annualized_volatility,
                "sharpe_ratio": sharpe_ratio,
                "maximum_drawdown": maximum_drawdown,
            }
        )

    return results


def create_report(metrics, start_date, end_date):
    best_return = max(
        metrics,
        key=lambda item: item["total_return"],
    )

    lowest_volatility = min(
        metrics,
        key=lambda item: item["annualized_volatility"],
    )

    best_sharpe = max(
        metrics,
        key=lambda item: item["sharpe_ratio"],
    )

    largest_drawdown = min(
        metrics,
        key=lambda item: item["maximum_drawdown"],
    )

    lines = [
        "# 股票收益与风险分析报告",
        "",
        f"**分析区间：** {start_date} 至 {end_date}",
        "",
        "本报告根据项目 SQLite 数据库中的历史股价数据"
        "自动生成。",
        "",
        "## 一、收益与风险指标",
        "",
        "| 股票代码 | 区间累计收益率 | 年化波动率 "
        "| 夏普比率 | 最大回撤 |",
        "|---|---:|---:|---:|---:|",
    ]

    for item in metrics:
        lines.append(
            f"| {item['ticker']} "
            f"| {item['total_return']:.2%} "
            f"| {item['annualized_volatility']:.2%} "
            f"| {item['sharpe_ratio']:.2f} "
            f"| {item['maximum_drawdown']:.2%} |"
        )

    lines.extend(
        [
            "",
            "## 二、主要发现",
            "",
            f"- **区间累计收益率最高：** "
            f"{best_return['ticker']}，"
            f"累计收益率为 {best_return['total_return']:.2%}。",
            f"- **年化波动率最低：** "
            f"{lowest_volatility['ticker']}，"
            f"年化波动率为 "
            f"{lowest_volatility['annualized_volatility']:.2%}。",
            f"- **夏普比率最高：** "
            f"{best_sharpe['ticker']}，"
            f"夏普比率为 {best_sharpe['sharpe_ratio']:.2f}。",
            f"- **历史最大回撤幅度最大：** "
            f"{largest_drawdown['ticker']}，"
            f"最大回撤为 "
            f"{largest_drawdown['maximum_drawdown']:.2%}。",
            "",
            "从历史结果来看，夏普比率最高的股票在承担"
            "每单位波动风险时获得了更高的收益，但较大的"
            "最大回撤也意味着投资者可能需要承受更加严重的"
            "阶段性亏损。",
            "",
            "## 三、投资价值变化",
            "",
            "下图假设在分析区间开始时，分别对每只股票"
            "投入100美元，并展示投资价值随时间的变化。",
            "",
            "![100美元投资价值变化]"
            "(figures/stock_performance.png)",
            "",
            "## 四、计算方法",
            "",
            "- 所有收益指标均使用调整后收盘价计算。",
            "- 区间累计收益率衡量整个分析期内的价格变化。",
            "- 年化波动率按照每年252个交易日计算。",
            "- 夏普比率暂时假设无风险利率为0%。",
            "- 最大回撤衡量投资价值从历史高点到后续低点的"
            "最大跌幅。",
            "",
            "## 五、注意事项",
            "",
            "本报告只根据历史价格数据进行统计分析，不构成"
            "投资建议。历史表现不能保证未来收益。",
            "",
        ]
    )

    return "\n".join(lines)

def main():
    with sqlite3.connect(DATABASE_PATH) as connection:
        prices = pd.read_sql_query(
            """
            SELECT ticker, date, adjusted_close
            FROM daily_prices
            ORDER BY ticker, date;
            """,
            connection,
            parse_dates=["date"],
        )

    metrics = calculate_metrics(prices)

    start_date = prices["date"].min().strftime("%Y-%m-%d")
    end_date = prices["date"].max().strftime("%Y-%m-%d")

    report = create_report(
        metrics,
        start_date,
        end_date,
    )

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_PATH.write_text(
        report,
        encoding="utf-8",
    )

    print("Report generated successfully.")
    print(f"Report path: {REPORT_PATH}")


if __name__ == "__main__":
    main()