from alpha_vantage_client import client
from datetime import datetime, timedelta

def get_daily_ohlcv(symbol: str, days: int = 30) -> dict:
    """
    Retrieves daily OHLCV data (open, high, low, close, volume) for a stock.
    """
    # Use free endpoint: TIME_SERIES_DAILY (not adjusted)
    data = client._request(
        function="TIME_SERIES_DAILY",
        params={"symbol": symbol, "outputsize": "compact"}
    )

    time_series_key = "Time Series (Daily)"
    if time_series_key not in data:
        return {"error": "No data available"}

    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    filtered_data = {}
    for date, values in data[time_series_key].items():
        if date >= cutoff_date:
            filtered_data[date] = {
                "open": values["1. open"],
                "high": values["2. high"],
                "low": values["3. low"],
                "close": values["4. close"],
                "volume": values["5. volume"]  # Fixed: 5. volume (free endpoint)
            }

    return {
        "symbol": symbol,
        "days": days,
        "data": filtered_data
    }


def get_technical_indicator(symbol: str, indicator: str, interval: str = "daily") -> dict:
    """
    获取股票的技术指标（如RSI、MACD等）

    Args:
        symbol: 股票代码
        indicator: 指标名称（如RSI、MACD）
        interval: 时间间隔（daily, weekly, monthly）

    Returns:
        包含指标数据的字典
    """
    indicator_mapping = {
        "RSI": "RSI",
        "MACD": "MACD",
        "SMA": "SMA",
        "BBANDS": "BBANDS"
    }

    if indicator not in indicator_mapping:
        return {"error": f"Unsupported indicator: {indicator}"}

    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": 14,  # 默认周期
        "series_type": "close"
    }

    # 特殊参数处理（例如MACD不需要time_period）
    if indicator == "MACD":
        params.pop("time_period")

    data = client._request(
        function=indicator_mapping[indicator],
        params=params
    )

    return {
        "symbol": symbol,
        "indicator": indicator,
        "data": data
    }

# Testing
if __name__ == "__main__":
    import pprint  # For pretty-printing complex data structures

    # Test parameters
    TEST_SYMBOL = "MSFT"  # Microsoft as test ticker
    TEST_DAYS = 2        # Test with last 5 days of data
    TEST_INDICATOR = "RSI"  # Test RSI indicator
    TEST_INTERVAL = "daily"

    print("===== Testing get_daily_ohlcv =====")
    ohlcv_data = get_daily_ohlcv(TEST_SYMBOL, TEST_DAYS)
    print(ohlcv_data)
    # try:
    #     ohlcv_data = get_daily_ohlcv(TEST_SYMBOL, TEST_DAYS)
    #     if "error" in ohlcv_data:
    #         print(f"Error: {ohlcv_data['error']}")
    #     else:
    #         print(f"Successfully retrieved {ohlcv_data['days']} days of data for {ohlcv_data['symbol']}")
    #         print("Latest 2 entries:")
    #         # Get the most recent 2 dates (sorted in descending order)
    #         recent_dates = sorted(ohlcv_data['data'].keys(), reverse=True)[:2]
    #         for date in recent_dates:
    #             print(f"\nDate: {date}")
    #             pprint.pprint(ohlcv_data['data'][date])  # Pretty-print the data
    # except Exception as e:
    #     print(f"get_daily_ohlcv test failed: {str(e)}")

    print("\n===== Testing get_technical_indicator =====")
    indicator_data = get_technical_indicator(TEST_SYMBOL, TEST_INDICATOR, TEST_INTERVAL)
    print(indicator_data[0])
    # try:
    #     indicator_data = get_technical_indicator(TEST_SYMBOL, TEST_INDICATOR, TEST_INTERVAL)
    #     if "error" in indicator_data:
    #         print(f"Error: {indicator_data['error']}")
    #     else:
    #         print(f"Successfully retrieved {indicator_data['indicator']} data for {indicator_data['symbol']}")
    #         print("Latest 2 indicator entries:")
    #
    #         # Fixed: Reliably find the RSI technical analysis key
    #         # RSI's key in the response is "Technical Analysis: RSI"
    #         tech_key = f"Technical Analysis: {TEST_INDICATOR}"
    #         if tech_key not in indicator_data['data']:
    #             print(f"Error: {tech_key} not found in response")
    #         else:
    #             # Get most recent 2 entries (sorted by date descending)
    #             recent_entries = sorted(
    #                 indicator_data['data'][tech_key].items(),
    #                 key=lambda x: x[0],
    #                 reverse=True
    #             )[:2]
    #             for date, values in recent_entries:
    #                 print(f"\nDate: {date}")
    #                 pprint.pprint(values)  # e.g., {'RSI': '52.34'}
    # except Exception as e:
    #     print(f"get_technical_indicator test failed: {str(e)}")