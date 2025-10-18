from alpha_vantage_client import client
from datetime import datetime, timedelta


def get_company_news(symbol: str, days: int = 7) -> dict:
    """
    获取公司相关新闻

    Args:
        symbol: 股票代码
        days: 回溯天数

    Returns:
        包含新闻列表的字典
    """
    # 计算日期范围（Alpha Vantage的新闻接口使用ISO格式）
    end_date = datetime.now().strftime("%Y%m%dT%H%M")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%dT%H%M")

    data = client._request(
        function="NEWS_SENTIMENT",
        params={
            "tickers": symbol,
            "time_from": start_date,
            "time_to": end_date,
            "limit": 20  # 最多返回20条
        }
    )

    # 提取关键信息
    news_items = []
    if "feed" in data:
        for item in data["feed"]:
            news_items.append({
                "title": item.get("title"),
                "source": item.get("source"),
                "time_published": item.get("time_published"),
                "summary": item.get("summary"),
                "url": item.get("url"),
                "sentiment": item.get("overall_sentiment_label")
            })

    return {
        "symbol": symbol,
        "days": days,
        "news_count": len(news_items),
        "news": news_items
    }


def get_market_news(category: str = "equities", limit: int = 10) -> dict:
    """
    获取市场整体新闻

    Args:
        category: 新闻类别（equities, forex, cryptocurrencies等）
        limit: 最多返回数量

    Returns:
        包含新闻列表的字典
    """
    data = client._request(
        function="NEWS_SENTIMENT",
        params={
            "topics": category,
            "limit": limit
        }
    )

    news_items = []
    if "feed" in data:
        for item in data["feed"]:
            news_items.append({
                "title": item.get("title"),
                "source": item.get("source"),
                "time_published": item.get("time_published"),
                "summary": item.get("summary"),
                "url": item.get("url"),
                "related_tickers": item.get("tickers", [])
            })

    return {
        "category": category,
        "news_count": len(news_items),
        "news": news_items
    }

#Testing
if __name__ == "__main__":
    import pprint  # For readable output of nested dictionaries

    # Test parameters
    TEST_SYMBOL = "MSFT"  # Company to test (Microsoft)
    TEST_NEWS_DAYS = 3  # Check news from last 3 days
    TEST_MARKET_CATEGORY = "equities"  # Market news category
    TEST_MARKET_LIMIT = 5  # Limit market news to 5 items

    # Test 1: get_company_news
    print("===== Testing get_company_news =====")
    try:
        company_news = get_company_news(TEST_SYMBOL, TEST_NEWS_DAYS)

        if "error" in company_news:
            print(f"Error: {company_news['error']}")
        else:
            print(
                f"Successfully retrieved {company_news['news_count']} news items for {company_news['symbol']} (last {company_news['days']} days)")

            # Print first 2 news items if available
            if company_news["news_count"] > 0:
                print("\nLatest 2 news items:")
                for i, news in enumerate(company_news["news"][:2], 1):
                    print(f"\nNews {i}:")
                    pprint.pprint({
                        "Title": news["title"],
                        "Source": news["source"],
                        "Published": news["time_published"],
                        "Sentiment": news["sentiment"]
                    })
            else:
                print("No news items found for the given period.")

    except Exception as e:
        print(f"get_company_news test failed: {str(e)}")

    # Test 2: get_market_news
    print("\n===== Testing get_market_news =====")
    try:
        market_news = get_market_news(TEST_MARKET_CATEGORY, TEST_MARKET_LIMIT)

        if "error" in market_news:
            print(f"Error: {market_news['error']}")
        else:
            print(
                f"Successfully retrieved {market_news['news_count']} market news items (category: {market_news['category']})")

            # Print first 2 market news items if available
            if market_news["news_count"] > 0:
                print("\nLatest 2 market news items:")
                for i, news in enumerate(market_news["news"][:2], 1):
                    print(f"\nNews {i}:")
                    pprint.pprint({
                        "Title": news["title"],
                        "Source": news["source"],
                        "Published": news["time_published"],
                        "Related Tickers": news["related_tickers"][:3]  # Show first 3 tickers
                    })
            else:
                print("No market news items found for the given category.")

    except Exception as e:
        print(f"get_market_news test failed: {str(e)}")