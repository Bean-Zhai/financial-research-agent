import re

from src.agent.tools import (
    compare_stocks,
    get_latest_prices,
    get_stock_metrics,
)


SUPPORTED_TICKERS = ["AAPL", "MSFT", "NVDA"]


def extract_tickers(question):
    question = question.upper()

    return [
        ticker
        for ticker in SUPPORTED_TICKERS
        if ticker in question
    ]


def format_stock_metrics(result):
    if not result["success"]:
        return result["error"]

    return (
        f"{result['ticker']}在"
        f"{result['start_date']}至{result['end_date']}期间：\n"
        f"- 区间累计收益率："
        f"{result['total_return']:.2%}\n"
        f"- 年化波动率："
        f"{result['annualized_volatility']:.2%}\n"
        f"- 夏普比率："
        f"{result['sharpe_ratio']:.2f}\n"
        f"- 最大回撤："
        f"{result['maximum_drawdown']:.2%}"
    )


def format_latest_prices(result):
    if not result["success"]:
        return result["error"]

    lines = [
        f"{result['ticker']}最近"
        f"{result['number_of_records']}个交易日的价格："
    ]

    for item in result["prices"]:
        lines.append(
            f"- {item['date']}："
            f"收盘价 ${item['close']:.2f}，"
            f"成交量 {item['volume']:,}"
        )

    return "\n".join(lines)


def format_comparison(result):
    if not result["success"]:
        return result["error"]

    comparison = result["comparison"]

    lines = ["股票比较结果：", ""]

    for stock in result["stocks"]:
        lines.append(
            f"- {stock['ticker']}："
            f"累计收益率 {stock['total_return']:.2%}，"
            f"年化波动率 "
            f"{stock['annualized_volatility']:.2%}，"
            f"夏普比率 {stock['sharpe_ratio']:.2f}，"
            f"最大回撤 "
            f"{stock['maximum_drawdown']:.2%}"
        )

    lines.extend(
        [
            "",
            f"累计收益率最高："
            f"{comparison['highest_return']}",
            f"年化波动率最低："
            f"{comparison['lowest_volatility']}",
            f"夏普比率最高："
            f"{comparison['highest_sharpe_ratio']}",
            f"最大回撤幅度最小："
            f"{comparison['smallest_maximum_drawdown']}",
        ]
    )

    return "\n".join(lines)


def answer_question(question):
    tickers = extract_tickers(question)
    normalized_question = question.lower()

    comparison_keywords = [
        "比较",
        "对比",
        "compare",
        "哪个好",
    ]

    latest_price_keywords = [
        "最近",
        "最新",
        "股价",
        "价格",
        "price",
    ]

    metrics_keywords = [
        "收益",
        "风险",
        "波动率",
        "夏普",
        "回撤",
        "表现",
        "指标",
    ]

    if any(
        keyword in normalized_question
        for keyword in comparison_keywords
    ):
        if len(tickers) < 2:
            return "请至少输入两只股票进行比较。"

        result = compare_stocks(tickers)
        return format_comparison(result)

    if any(
        keyword in normalized_question
        for keyword in latest_price_keywords
    ):
        if not tickers:
            return "请告诉我需要查询哪只股票。"

        number_match = re.search(r"\d+", question)
        limit = int(number_match.group()) if number_match else 5

        result = get_latest_prices(tickers[0], limit)
        return format_latest_prices(result)

    if any(
        keyword in normalized_question
        for keyword in metrics_keywords
    ):
        if not tickers:
            return "请告诉我需要分析哪只股票。"

        result = get_stock_metrics(tickers[0])
        return format_stock_metrics(result)

    if len(tickers) == 1:
        result = get_stock_metrics(tickers[0])
        return format_stock_metrics(result)

    return (
        "我暂时无法判断你需要什么分析。"
        "目前支持股价查询、收益风险分析和多股票比较。"
    )


def main():
    print("Financial Research Agent")
    print("输入 quit 可以退出。\n")

    while True:
        question = input("你：").strip()

        if question.lower() in ["quit", "exit", "退出"]:
            print("Agent：再见！")
            break

        if not question:
            continue

        answer = answer_question(question)
        print(f"\nAgent：{answer}\n")


if __name__ == "__main__":
    main()