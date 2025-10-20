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
    get_random_a_share_sequence,   # 零参数函数（内部固定逻辑）
)

# =========================
# 行情 & 新闻：字符串(JSON)参数——保持不变
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
            'Example: {"symbol":"600519.SH","start_date":"2025-01-01","adj":"qfq","prefer":["akshare","tushare"]}'
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
# 随机行业挑股：永久固定输入 "1"
# =========================

class RandomIndustryAlwaysOne(BaseModel):
    one: str = Field(
        default="1",
        description=(
            "you do not need to change this parameter; "
        ),
    )

@tool(
    name_or_callable="a_share_random_industry_picks",
    description=(
        "This tool can get the targeted stock list of A-share market."
    ),
    args_schema=RandomIndustryAlwaysOne,
    return_direct=False,
)
def a_share_random_industry_picks_tool(one: str = "1") -> Dict[str, Any]:
    """Fixed-parameter tool. The string input '1' is required by the framework but ignored by the logic."""
    # 忽略 one，无论传什么都执行固定逻辑
    return get_random_a_share_sequence()

# # 导出一个工具列表，便于一键注册到 Agent
# TOOLS: List[Any] = [
#     a_share_market_data_tool,
#     a_share_company_news_tool,
#     a_share_random_industry_picks_tool,
# ]
