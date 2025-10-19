# ──────────────────────────────────────────────────────────────────────────────
# File: alpha_vantage_agent/tools/tool_specs.py
# LangChain @tool decorator + Pydantic args_schema (with descriptions)
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

from typing import Optional, Literal, Dict, Any, List
from pydantic import BaseModel, Field
from langchain.tools import tool

# 复用已导出的业务函数（请确保 alpha_vantage_client 路径可导入）
from alpha_vantage_client import client
from stock_agent.tools.news_tools import get_market_news, get_company_news
from stock_agent.tools.stock_data_tools import get_technical_indicator, get_daily_ohlcv
from stock_agent.tools.stock_picker import search_stocks


# =========================
# 参数模型（含 description）
# =========================

class SearchStocksArgs(BaseModel):
    keywords: str = Field(
        default="stock",
        description="Search term for stocks, e.g., 'healthcare', 'technology'. Defaults to 'stock' if empty.",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results to return. Range: 1-50.",
    )


class GetDailyOhlcvArgs(BaseModel):
    symbol: str = Field(
        ...,
        description="Stock symbol (ticker), e.g., 'MSFT' for Microsoft, 'AAPL' for Apple.",
    )
    days: int = Field(
        default=30,
        ge=1,
        le=90,
        description="Number of historical days to fetch OHLCV data. Range: 1-90.",
    )


class GetTechnicalIndicatorArgs(BaseModel):
    symbol: str = Field(
        ...,
        description="Stock symbol (ticker), e.g., 'MSFT' for Microsoft, 'AAPL' for Apple.",
    )
    indicator: Literal["RSI", "MACD", "SMA", "BBANDS"] = Field(
        ...,
        description="Technical indicator to retrieve. Only supports 'RSI', 'MACD', 'SMA', 'BBANDS'.",
    )
    interval: Literal["daily", "weekly", "monthly"] = Field(
        default="daily",
        description="Time interval for the indicator. Options: 'daily', 'weekly', 'monthly'.",
    )


class GetCompanyNewsArgs(BaseModel):
    symbol: str = Field(
        ...,
        description="Stock symbol (ticker) of the target company, e.g., 'MSFT' for Microsoft.",
    )
    days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Number of historical days to fetch news. Range: 1-30. Max 20 news items returned.",
    )


class GetMarketNewsArgs(BaseModel):
    category: Literal["equities", "forex", "cryptocurrencies"] = Field(
        default="equities",
        description="Market news category. Options: 'equities', 'forex', 'cryptocurrencies'.",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum number of market news items to return. Range: 1-20.",
    )


# =========================
# 工具定义（@tool + description）
# =========================

@tool(
    name_or_callable="alpha_vantage_search_stocks",
    description="Search global stocks by keywords (e.g., industry, company name) and return formatted {code: symbol, name: company name} list.",
    args_schema=SearchStocksArgs,
    return_direct=False,
)
def alpha_vantage_search_stocks_tool(
    keywords: str = "stock",
    limit: int = 10,
) -> List[Dict[str, str]]:
    """Return filtered stock list by search keywords, with configurable result count."""
    return search_stocks(keywords=keywords, limit=limit)


@tool(
    name_or_callable="alpha_vantage_get_daily_ohlcv",
    description="Retrieve daily OHLCV (open, high, low, close, volume) data for a specific stock, filtered by historical days.",
    args_schema=GetDailyOhlcvArgs,
    return_direct=False,
)
def alpha_vantage_get_daily_ohlcv_tool(
    symbol: str,
    days: int = 30,
) -> Dict[str, Any]:
    """Return daily OHLCV data for the given stock, capped at the specified number of days."""
    return get_daily_ohlcv(symbol=symbol, days=days)


@tool(
    name_or_callable="alpha_vantage_get_technical_indicator",
    description="Fetch common technical indicators (RSI/MACD/SMA/BBANDS) for a stock, with configurable time intervals.",
    args_schema=GetTechnicalIndicatorArgs,
    return_direct=False,
)
def alpha_vantage_get_technical_indicator_tool(
    symbol: str,
    indicator: Literal["RSI", "MACD", "SMA", "BBANDS"],
    interval: Literal["daily", "weekly", "monthly"] = "daily",
) -> Dict[str, Any]:
    """Return technical indicator data for the given stock, supporting daily/weekly/monthly intervals."""
    return get_technical_indicator(symbol=symbol, indicator=indicator, interval=interval)


@tool(
    name_or_callable="alpha_vantage_get_company_news",
    description="Get recent news (with sentiment) for a specific company, filtered by historical days (max 20 news items).",
    args_schema=GetCompanyNewsArgs,
    return_direct=False,
)
def alpha_vantage_get_company_news_tool(
    symbol: str,
    days: int = 7,
) -> Dict[str, Any]:
    """Return company-specific news with sentiment labels, capped at the specified number of days."""
    return get_company_news(symbol=symbol, days=days)


@tool(
    name_or_callable="alpha_vantage_get_market_news",
    description="Retrieve market-wide news by category (equities/forex/cryptocurrencies), with configurable result count.",
    args_schema=GetMarketNewsArgs,
    return_direct=False,
)
def alpha_vantage_get_market_news_tool(
    category: Literal["equities", "forex", "cryptocurrencies"] = "equities",
    limit: int = 10,
) -> Dict[str, Any]:
    """Return market news for the specified category, with configurable maximum results."""
    return get_market_news(category=category, limit=limit)


# 导出工具列表，便于一键注册到 Agent
ALPHA_VANTAGE_TOOLS: List[Any] = [
    alpha_vantage_search_stocks_tool,
    alpha_vantage_get_daily_ohlcv_tool,
    alpha_vantage_get_technical_indicator_tool,
    alpha_vantage_get_company_news_tool,
    alpha_vantage_get_market_news_tool,
]

# =========================
# 工具测试代码（兼容新版本调用方式）
# =========================
if __name__ == "__main__":
    import pprint
    from pprint import pprint

    print("="*50)
    print("Starting Alpha Vantage Tools Test")
    print("="*50)

    # 测试1: 股票搜索工具
    try:
        print("\n1. Testing alpha_vantage_search_stocks_tool...")
        # 新版本调用方式：使用 invoke 方法 + input 参数
        search_result = alpha_vantage_search_stocks_tool.invoke(
            input={
                "keywords": "technology",
                "limit": 5
            }
        )
        print(f"Found {len(search_result)} technology-related stocks:")
        pprint(search_result[:3])  # 显示前3条结果
    except Exception as e:
        print(f"Search stocks failed: {str(e)}")

    # 测试2: 日线OHLCV工具
    try:
        print("\n2. Testing alpha_vantage_get_daily_ohlcv_tool...")
        ohlcv_result = alpha_vantage_get_daily_ohlcv_tool.invoke(
            input={
                "symbol": "MSFT",
                "days": 5
            }
        )
        print(f"Fetched {len(ohlcv_result['data'])} days of data for {ohlcv_result['symbol']}")
        if ohlcv_result['data']:
            latest_date = max(ohlcv_result['data'].keys())
            print(f"Latest data ({latest_date}):")
            pprint(ohlcv_result['data'][latest_date])
    except Exception as e:
        print(f"Get daily OHLCV failed: {str(e)}")

    # 测试3: 技术指标工具
    try:
        print("\n3. Testing alpha_vantage_get_technical_indicator_tool...")
        indicator_result = alpha_vantage_get_technical_indicator_tool.invoke(
            input={
                "symbol": "AAPL",
                "indicator": "RSI",
                "interval": "daily"
            }
        )
        print(f"Fetched {indicator_result['indicator']} data for {indicator_result['symbol']}")
        if "Technical Analysis: RSI" in indicator_result['data']:
            latest_date = max(indicator_result['data']["Technical Analysis: RSI"].keys())
            print(f"Latest RSI ({latest_date}):")
            pprint(indicator_result['data']["Technical Analysis: RSI"][latest_date])
    except Exception as e:
        print(f"Get technical indicator failed: {str(e)}")

    # 测试4: 公司新闻工具
    try:
        print("\n4. Testing alpha_vantage_get_company_news_tool...")
        company_news_result = alpha_vantage_get_company_news_tool.invoke(
            input={
                "symbol": "GOOGL",
                "days": 3
            }
        )
        print(f"Found {company_news_result['news_count']} news items for {company_news_result['symbol']}")
        if company_news_result['news_count'] > 0:
            print("Latest news item:")
            pprint({
                "title": company_news_result['news'][0]['title'],
                "source": company_news_result['news'][0]['source'],
                "sentiment": company_news_result['news'][0]['sentiment']
            })
    except Exception as e:
        print(f"Get company news failed: {str(e)}")

    # 测试5: 市场新闻工具
    try:
        print("\n5. Testing alpha_vantage_get_market_news_tool...")
        market_news_result = alpha_vantage_get_market_news_tool.invoke(
            input={
                "category": "equities",
                "limit": 3
            }
        )
        print(f"Found {market_news_result['news_count']} market news items in {market_news_result['category']}")
        if market_news_result['news_count'] > 0:
            print("Latest market news:")
            pprint({
                "title": market_news_result['news'][0]['title'],
                "related_tickers": market_news_result['news'][0]['related_tickers'][:3]
            })
    except Exception as e:
        print(f"Get market news failed: {str(e)}")

    print("\n" + "="*50)
    print("Test completed")
    print("="*50)