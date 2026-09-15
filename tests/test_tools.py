import pytest

from src.agent.tools import (
    analyze_rolling_volatility,
    calculate_correlation,
    get_available_stocks,
    get_stock_metrics,
)


def test_available_stocks():
    result = get_available_stocks()

    assert result["success"] is True

    tickers = {
        stock["ticker"]
        for stock in result["stocks"]
    }

    assert {"AAPL", "MSFT", "NVDA"}.issubset(tickers)


def test_stock_metrics_with_date_range():
    result = get_stock_metrics(
        ticker="AAPL",
        start_date="2024-01-01",
        end_date="2024-12-31",
    )

    assert result["success"] is True
    assert result["ticker"] == "AAPL"
    assert result["start_date"] == "2024-01-02"
    assert result["end_date"] == "2024-12-31"
    assert result["trading_days"] > 200
    assert isinstance(result["total_return"], float)
    assert result["annualized_volatility"] > 0
    assert result["maximum_drawdown"] <= 0


def test_ticker_is_case_insensitive():
    result = get_stock_metrics("aapl")

    assert result["success"] is True
    assert result["ticker"] == "AAPL"


def test_unknown_ticker():
    result = get_stock_metrics("UNKNOWN")

    assert result["success"] is False
    assert "没有找到" in result["error"]


def test_invalid_date_format():
    result = get_stock_metrics(
        ticker="AAPL",
        start_date="2024/01/01",
        end_date="2024-12-31",
    )

    assert result["success"] is False
    assert "日期格式错误" in result["error"]


def test_reversed_date_range():
    result = get_stock_metrics(
        ticker="AAPL",
        start_date="2024-12-31",
        end_date="2024-01-01",
    )

    assert result["success"] is False
    assert "开始日期不能晚于结束日期" in result["error"]


def test_correlation_analysis():
    result = calculate_correlation(
        tickers=["AAPL", "MSFT", "NVDA"],
        start_date="2024-01-01",
        end_date="2024-12-31",
    )

    assert result["success"] is True

    matrix = result["correlation_matrix"]

    for ticker in ["AAPL", "MSFT", "NVDA"]:
        assert ticker in matrix

        assert matrix[ticker][ticker] == pytest.approx(
            1.0
        )

    lowest_pair = result[
        "lowest_correlation_pair"
    ]

    assert -1 <= lowest_pair["correlation"] <= 1


def test_rolling_volatility():
    result = analyze_rolling_volatility(
        tickers=["AAPL", "MSFT", "NVDA"],
        windows=[20, 60],
        start_date="2024-01-01",
        end_date="2024-12-31",
    )

    assert result["success"] is True

    for ticker in ["AAPL", "MSFT", "NVDA"]:
        assert ticker in result["results"]

        ticker_result = result["results"][ticker]

        assert "20_day" in ticker_result
        assert "60_day" in ticker_result

        assert (
            ticker_result["20_day"][
                "peak_volatility"
            ]
            > 0
        )