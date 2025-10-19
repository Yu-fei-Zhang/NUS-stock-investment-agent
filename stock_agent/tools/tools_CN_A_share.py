# ──────────────────────────────────────────────────────────────────────────────
# File: stock_agent/tools/tool_specs.py
# LangChain @tool decorator + Pydantic args_schema (with descriptions)
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

from typing import Optional, Literal, Dict, Any, List
from pydantic import BaseModel, Field
from langchain.tools import tool

# 复用你在包里已导出的业务函数（这些函数已支持“单字典参数”）
from stock_agent.tools import (
    get_stock_market_data_united,
    get_company_news_united,
    get_random_a_share_sequence,
)

# =========================
# 参数模型（单字段 params，集中写描述）
# =========================

class MarketDataParams(BaseModel):
    params: Dict[str, Any] = Field(
        ...,
        description=(
            "Input as a JSON-like dict for unified A-share daily OHLCV:\n"
            "- **symbol** (str, required): A-share ticker. Accepts '600519', '600519.SH', 'sh600519', etc.\n"
            "- **start_date** (str, optional): Start date, 'YYYY-MM-DD' or 'YYYYMMDD'.\n"
            "- **end_date** (str, optional): End date, 'YYYY-MM-DD' or 'YYYYMMDD' (capped at today).\n"
            "- **adj** (str, optional): Price adjustment mode. One of 'qfq' (default), 'hfq', 'none'.\n"
            "- **prefer** (List[str], optional): Vendor priority, e.g. ['akshare','tushare'].\n"
            "- **tushare_token** (str, optional): TuShare token if not set in env."
        ),
    )


class CompanyNewsParams(BaseModel):
    params: Dict[str, Any] = Field(
        ...,
        description=(
            "Input as a JSON-like dict for unified A-share company news (Eastmoney + Sina + AkShare):\n"
            "- **symbol_or_name** (str, required): Stock code or Chinese company name, e.g. '600519' or '贵州茅台'.\n"
            "- **limit** (int, optional, default 50): Max items to return (1–200).\n"
            "- **since** (str, optional): Start date inclusive, 'YYYY-MM-DD' or 'YYYYMMDD'.\n"
            "- **until** (str, optional): End date inclusive, 'YYYY-MM-DD' or 'YYYYMMDD'."
        ),
    )


class RandomIndustryParams(BaseModel):
    params: Dict[str, Any] = Field(
        ...,
        description=(
            "Input as a JSON-like dict to randomly pick industries and top movers per industry (Eastmoney constituents):\n"
            "- **limit_industries** (int, optional, default 5): How many industries to sample randomly (1–30 recommended).\n"
            "- **per_industry** (int, optional, default 5): How many stocks to pick per industry (top by same-day % change).\n"
            "- **seed** (int|null, optional): Fix seed for reproducible sampling; omit/null for different results each call.\n"
            "- **include_names** (bool, optional, default true): Include stock names along with codes.\n"
            "- **exclude_st** (bool, optional, default true): Exclude ST/‘退’ tagged stocks.\n"
            "- **hard_cap_total** (int|null, optional, default 30): Safety cap for total returned rows; set null to disable."
        ),
    )


# =========================
# 工具定义（@tool + description）
# =========================

@tool(
    name_or_callable="a_share_market_data",
    description="Fetch A-share daily OHLCV with a unified schema (supports pre/post adjustment). "
                "Pass a single dict argument named 'params'.",
    args_schema=MarketDataParams,
    return_direct=False,
)
def a_share_market_data_tool(params: Dict[str, Any]) -> Dict[str, Any]:
    """Return daily OHLCV for the given A-share symbol using a single dict input."""
    return get_stock_market_data_united(params)


@tool(
    name_or_callable="a_share_company_news",
    description="Aggregate A-share company news from Eastmoney + Sina + AkShare with a unified schema. "
                "Pass a single dict argument named 'params'.",
    args_schema=CompanyNewsParams,
    return_direct=False,
)
def a_share_company_news_tool(params: Dict[str, Any]) -> Dict[str, Any]:
    """Return merged company news given a stock code or Chinese name using a single dict input."""
    return get_company_news_united(params)


@tool(
    name_or_callable="a_share_random_industry_picks",
    description=(
        "Randomly sample industries from a fixed Eastmoney list and, for each industry, pick the top movers by same-day % change. "
        "Default behavior: sample 5 industries and pick 5 stocks per industry (total ≈25). "
        "Pass a single dict argument named 'params'."
    ),
    args_schema=RandomIndustryParams,
    return_direct=False,
)
def a_share_random_industry_picks_tool(params: Dict[str, Any]) -> Dict[str, Any]:
    """Randomly sample industries and return top-N stocks per industry (same-day % change priority)."""
    return get_random_a_share_sequence(params)


# 导出一个工具列表，便于一键注册到 Agent
TOOLS: List[Any] = [
    a_share_market_data_tool,
    a_share_company_news_tool,
    a_share_random_industry_picks_tool,
]
