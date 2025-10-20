# ──────────────────────────────────────────────────────────────────────────────
# File: stock_agent/tools/tool_specs.py
# LangChain @tool decorator + Pydantic args_schema (with descriptions)
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain.tools import tool
import json

# 复用你在包里已导出的业务函数
from stock_agent.tools import (
    get_stock_market_data_united,
    get_company_news_united,
    get_random_a_share_sequence,   # 现在是零参数函数
)

# =========================
# 行情 & 新闻：字符串(JSON)参数
# =========================

def _parse_json_params(params_json: str) -> Dict[str, Any]:
    try:
        data = json.loads(params_json)
    except Exception as e:
        raise ValueError(f"params_json is not valid JSON: {e}")
    if not isinstance(data, dict):
        raise ValueError("params_json must be a JSON object (e.g. '{\"key\":\"value\"}').")
    return data

class MarketDataParams(BaseModel):
    params_json: str = Field(
        ...,
        description=(
            "PASS EXACTLY ONE ARGUMENT named `params_json`, and it MUST be a JSON STRING encoding an OBJECT.\n"
            "Allowed keys: symbol (required), start_date, end_date, adj, prefer, tushare_token.\n"
            "Example: "
            '{"symbol":"600519.SH","start_date":"2025-01-01","adj":"qfq","prefer":["akshare","tushare"]}'
        ),
    )

class CompanyNewsParams(BaseModel):
    params_json: str = Field(
        ...,
        description=(
            "PASS EXACTLY ONE ARGUMENT named `params_json`, and it MUST be a JSON STRING encoding an OBJECT.\n"
            "Allowed keys: symbol_or_name (required), limit, since, until.\n"
            'Example: {"symbol_or_name":"600519","limit":20,"since":"2025-01-01"}'
        ),
    )

@tool(
    name_or_callable="a_share_market_data",
    description="Fetch A-share daily OHLCV with a unified schema. "
                "Pass a single JSON string argument named 'params_json'.",
    args_schema=MarketDataParams,
    return_direct=False,
)
def a_share_market_data_tool(params_json: str) -> Dict[str, Any]:
    params = _parse_json_params(params_json)
    return get_stock_market_data_united(params)

@tool(
    name_or_callable="a_share_company_news",
    description="Aggregate A-share company news from Eastmoney + Sina + AkShare. "
                "Pass a single JSON string argument named 'params_json'.",
    args_schema=CompanyNewsParams,
    return_direct=False,
)
def a_share_company_news_tool(params_json: str) -> Dict[str, Any]:
    params = _parse_json_params(params_json)
    return get_company_news_united(params)

# =========================
# 随机行业挑股：零参数工具
# =========================

@tool(
    name_or_callable="a_share_random_industry_picks",
    description=(
        "No real parameters. You MAY pass {} or an empty string. "
        "Randomly sample 5 industries and pick top 5 movers per industry (~25 stocks). "
        'Output: {"rows":[{"code":"XXXXXX","name":"Company","industry":"Industry"},...],"vendor_meta":{...}}'
    ),
    return_direct=False,
)
def a_share_random_industry_picks_tool(_ignored: Any = None) -> Dict[str, Any]:
    """Zero-arg tool. Any input is ignored (supports {}, '', None)."""
    return get_random_a_share_sequence()

# 导出一个工具列表，便于一键注册到 Agent
TOOLS: List[Any] = [
    a_share_market_data_tool,
    a_share_company_news_tool,
    a_share_random_industry_picks_tool,
]
