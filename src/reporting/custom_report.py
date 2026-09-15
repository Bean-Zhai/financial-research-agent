from pathlib import Path

from src.agent.tools import (
    analyze_rolling_volatility,
    calculate_correlation,
    compare_stocks,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

REPORT_DIRECTORY = (
    PROJECT_ROOT / "reports" / "generated"
)


def generate_custom_report(
    tickers,
    start_date=None,
    end_date=None,
):
    performance = compare_stocks(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
    )

    if not performance["success"]:
        return performance

    stocks = performance["stocks"]

    valid_tickers = [
        stock["ticker"]
        for stock in stocks
    ]

    actual_start_date = min(
        stock["start_date"]
        for stock in stocks
    )

    actual_end_date = max(
        stock["end_date"]
        for stock in stocks
    )

    lines = [
        "# 股票定制研究报告",
        "",
        f"**分析股票：** {', '.join(valid_tickers)}",
        "",
        (
            f"**实际分析区间：** "
            f"{actual_start_date} 至 {actual_end_date}"
        ),
        "",
        "## 一、收益与风险概览",
        "",
        (
            "| 股票 | 累计收益率 | 年化波动率 "
            "| 夏普比率 | 最大回撤 |"
        ),
        "|---|---:|---:|---:|---:|",
    ]

    for stock in stocks:
        lines.append(
            f"| {stock['ticker']} "
            f"| {stock['total_return']:.2%} "
            f"| {stock['annualized_volatility']:.2%} "
            f"| {stock['sharpe_ratio']:.2f} "
            f"| {stock['maximum_drawdown']:.2%} |"
        )

    comparison = performance["comparison"]

    lines.extend(
        [
            "",
            "## 二、主要发现",
            "",
            (
                f"- 累计收益率最高："
                f"**{comparison['highest_return']}**。"
            ),
            (
                f"- 年化波动率最低："
                f"**{comparison['lowest_volatility']}**。"
            ),
            (
                f"- 夏普比率最高："
                f"**{comparison['highest_sharpe_ratio']}**。"
            ),
            (
                f"- 最大回撤幅度最小："
                f"**{comparison['smallest_maximum_drawdown']}**。"
            ),
        ]
    )

    if len(valid_tickers) >= 2:
        correlation = calculate_correlation(
            tickers=valid_tickers,
            start_date=start_date,
            end_date=end_date,
        )

        if correlation["success"]:
            matrix = correlation["correlation_matrix"]
            matrix_tickers = list(matrix.keys())

            lines.extend(
                [
                    "",
                    "## 三、收益率相关性",
                    "",
                    (
                        "| 股票 | "
                        + " | ".join(matrix_tickers)
                        + " |"
                    ),
                    (
                        "|---|"
                        + "---:|" * len(matrix_tickers)
                    ),
                ]
            )

            for row_ticker in matrix_tickers:
                values = []

                for column_ticker in matrix_tickers:
                    correlation_value = matrix[
                        column_ticker
                    ][row_ticker]

                    values.append(
                        f"{correlation_value:.2f}"
                    )

                lines.append(
                    f"| {row_ticker} | "
                    + " | ".join(values)
                    + " |"
                )

            lowest_pair = correlation[
                "lowest_correlation_pair"
            ]

            lines.extend(
                [
                    "",
                    (
                        "历史收益率相关性最低的组合为"
                        f" **{lowest_pair['first_ticker']}** 与"
                        f" **{lowest_pair['second_ticker']}**，"
                        "相关系数为"
                        f" {lowest_pair['correlation']:.2f}。"
                    ),
                    "",
                    (
                        "较低的相关性通常意味着相对更好的"
                        "分散化效果，但相关关系可能随时间变化。"
                    ),
                ]
            )

    rolling = analyze_rolling_volatility(
        tickers=valid_tickers,
        windows=[20, 60],
        start_date=start_date,
        end_date=end_date,
    )

    if rolling["success"]:
        lines.extend(
            [
                "",
                "## 四、滚动波动率峰值",
                "",
                (
                    "| 股票 | 窗口 | 峰值年化波动率 "
                    "| 峰值日期 |"
                ),
                "|---|---:|---:|---:|",
            ]
        )

        for ticker, ticker_result in rolling[
            "results"
        ].items():
            for window_name, result in (
                ticker_result.items()
            ):
                window = window_name.replace(
                    "_day",
                    "日",
                )

                lines.append(
                    f"| {ticker} "
                    f"| {window} "
                    f"| {result['peak_volatility']:.2%} "
                    f"| {result['peak_date']} |"
                )

    lines.extend(
        [
            "",
            "## 五、方法与限制",
            "",
            "- 收益指标使用调整后收盘价计算。",
            "- 年化波动率按每年252个交易日计算。",
            "- 夏普比率暂时假设无风险利率为0%。",
            "- 相关性使用每日收益率计算。",
            "- 20日和60日滚动波动率分别反映较短期"
            "和较中期的风险变化。",
            "- 本报告仅基于历史价格数据，不构成投资建议。",
            "",
        ]
    )

    REPORT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    ticker_part = "_".join(valid_tickers)

    date_part = (
        f"{actual_start_date}_{actual_end_date}"
    )

    report_path = (
        REPORT_DIRECTORY
        / f"report_{ticker_part}_{date_part}.md"
    )

    report_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return {
        "success": True,
        "report_path": str(report_path),
        "tickers": valid_tickers,
        "start_date": actual_start_date,
        "end_date": actual_end_date,
    }


if __name__ == "__main__":
    result = generate_custom_report(
        tickers=["AAPL", "MSFT", "NVDA"],
        start_date="2024-01-01",
        end_date="2024-12-31",
    )

    print(result)