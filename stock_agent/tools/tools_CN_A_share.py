# ──────────────────────────────────────────────────────────────────────────────
# File: stock_agent/tools/tool_specs.py
# LangChain @tool decorator + Pydantic args_schema (with descriptions)
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

from typing import Optional, Literal, Dict, Any, List
from pydantic import BaseModel, Field
from langchain.tools import tool

# 复用你在包里已导出的业务函数
from stock_agent.tools import (
    get_stock_market_data_united,
    get_company_news_united,
    list_a_share_industry_keywords,
    get_a_share_list_by_exact_industry,
)

# =========================
# 参数模型（含 description）
# =========================

class MarketDataArgs(BaseModel):
    symbol: str = Field(
        ...,
        description="A-share symbol. Accepts '600519', '600519.SH', 'sh600519', etc.",
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start date (YYYY-MM-DD or YYYYMMDD). Optional.",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date (YYYY-MM-DD or YYYYMMDD). Optional; capped at today.",
    )
    adj: Literal["qfq", "hfq", "none"] = Field(
        default="qfq",
        description="Price adjustment mode: 'qfq' (pre-adjust), 'hfq' (post-adjust), or 'none'.",
    )


class CompanyNewsArgs(BaseModel):
    symbol_or_name: str = Field(
        ...,
        description="Stock code or Chinese company name, e.g., '600519' or '贵州茅台'.",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of news items to return.",
    )
    since: Optional[str] = Field(
        default=None,
        description="Start date inclusive (YYYY-MM-DD or YYYYMMDD). Optional.",
    )
    until: Optional[str] = Field(
        default=None,
        description="End date inclusive (YYYY-MM-DD or YYYYMMDD). Optional.",
    )


class ExactIndustryArgs(BaseModel):
    industry_name: str = Field(
        ...,
        description="Exact industry name from a_share_list_industries (the 'industry' field).",
    )
    limit: int = Field(
        default=30,
        ge=1,
        le=200,
        description="Maximum number of constituents to return.",
    )
    include_names: bool = Field(
        default=False,
        description="If true, also include company names alongside codes.",
    )


# =========================
# 工具定义（@tool + description）
# =========================

@tool(
    name_or_callable="a_share_market_data",
    description="Fetch A-share daily OHLCV with a unified schema (supports pre/post adjustment).",
    args_schema=MarketDataArgs,
    return_direct=False,
)
def a_share_market_data_tool(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    adj: str = "qfq",
) -> Dict[str, Any]:
    """Return daily OHLCV for a given A-share symbol. Supports 'qfq'/'hfq'/'none'."""
    return get_stock_market_data_united(symbol, start_date, end_date, adj)


@tool(
    name_or_callable="a_share_company_news",
    description="Aggregate A-share company news from Eastmoney + Sina + AkShare, returned in a unified schema.",
    args_schema=CompanyNewsArgs,
    return_direct=False,
)
def a_share_company_news_tool(
    symbol_or_name: str,
    limit: int = 50,
    since: Optional[str] = None,
    until: Optional[str] = None,
) -> Dict[str, Any]:
    """Return merged company news given a stock code or Chinese name, with optional date filters."""
    return get_company_news_united(symbol_or_name, limit=limit, since=since, until=until)


@tool(
    name_or_callable="a_share_list_industries",
    description="List all available A-share industry keywords (industry, code) from Eastmoney/AkShare.",
    return_direct=False,
)
def a_share_list_industries_tool() -> Dict[str, Any]:
    """Return the full catalog of industry keywords. Use one of them in the next tool."""
    return list_a_share_industry_keywords()


@tool(
    name_or_callable="a_share_constituents_by_industry",
    description="Get A-share constituents by an exact industry name selected from the catalog.",
    args_schema=ExactIndustryArgs,
    return_direct=False,
)
def a_share_constituents_by_industry_tool(
    industry_name: str,
    limit: int = 30,
    include_names: bool = False,
) -> Dict[str, Any]:
    """Return constituent codes (and optionally names) for a given exact industry name."""
    return get_a_share_list_by_exact_industry(
        industry_name=industry_name,
        limit=limit,
        include_names=include_names,
    )


# 导出一个工具列表，便于一键注册到 Agent
TOOLS: List[Any] = [
    a_share_market_data_tool,
    a_share_company_news_tool,
    a_share_list_industries_tool,
    a_share_constituents_by_industry_tool,
]
