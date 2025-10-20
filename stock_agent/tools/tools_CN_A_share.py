# ──────────────────────────────────────────────────────────────────────────────
# File: stock_agent/tools/tools_CN_A_share.py
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
# 行情 & 新闻：字符串(JSON)参数——保持不变（仅更新描述）
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
            "➤ **Input must be the stock code returned by `a_share_random_industry_picks_tool`** (pick one from its `rows`).\n"
            "   Use it as the value of the `symbol` key.\n"
            "   Examples of `params_json`:\n"
            '   - {"symbol":"600519"}\n'
            '   - {"symbol":"600519.SH"}\n\n'
            "Other optional keys (if supported by your runtime): `start_date`, `end_date`, `adj`, `prefer`, `tushare_token`.\n"
            "If omitted, the tool implementation defaults to the **last two weeks** window and 'qfq' adjustment."
        ),
    )

class CompanyNewsParams(BaseModel):
    params_json: str = Field(
        ...,
        description=(
            "PASS EXACTLY ONE ARGUMENT named `params_json`, and it MUST be a JSON STRING encoding an OBJECT.\n"
            "➤ **Input must be the stock code returned by `a_share_random_industry_picks_tool`** (pick one from its `rows`).\n"
            "   Put that code under the `symbol_or_name` key.\n"
            "   Examples of `params_json`:\n"
            '   - {"symbol_or_name":"600519"}\n'
            '   - {"symbol_or_name":"600519.SH"}\n\n'
            "Optional keys you may include: `limit`, `since`, `until`.\n"
            "If omitted, the tool implementation defaults to the window **from 2024-10-01 up to today**."
        ),
    )

@tool(
    name_or_callable="a_share_market_data",
    description=(
        "Fetch A-share daily OHLCV with a unified schema.\n"
        "👉 **Usage flow:** First call `a_share_random_industry_picks_tool` to obtain a stock list, "
        "then pick one code from its `rows` and pass it here via `params_json`, e.g. `{\"symbol\":\"600519\"}`.\n"
        "👉 **Output:** JSON with fields: `symbol`, `rows` (list of bars with `date, open, high, low, close, volume, amount, adj_factor`), "
        "and `vendor_meta` (source/latency/effective params). By default, the date range is the **last two weeks**."
    ),
    args_schema=MarketDataParams,
    return_direct=False,
)
def a_share_market_data_tool(params_json: str) -> Dict[str, Any]:
    """
    Call this tool **after** `a_share_random_industry_picks_tool`.
    Pick one stock code from its `rows`, and pass it as:
      params_json = '{"symbol":"600519"}'  (or '{"symbol":"600519.SH"}')

    Output:
      {
        "symbol": "<the input code>",
        "rows": [
          {"date":"YYYY-MM-DD","open":...,"high":...,"low":...,"close":...,"volume":...,"amount":...,"adj_factor":...},
          ...
        ],
        "vendor_meta": {...}
      }
    """
    params = _parse_json_params(params_json)
    return get_stock_market_data_united(params)

@tool(
    name_or_callable="a_share_company_news",
    description=(
        "Aggregate A-share company news from Eastmoney + Sina + AkShare.\n"
        "👉 **Usage flow:** First call `a_share_random_industry_picks_tool` to obtain a stock list, "
        "then pick one code from its `rows` and pass it here via `params_json`, e.g. `{\"symbol_or_name\":\"600519\"}`.\n"
        "👉 **Output:** JSON with fields: `symbol`, and `rows` (each item includes `published_at, title, summary, url, source, symbol, company_name`), "
        "plus `vendor_meta` (source/window). By default, the date range is **2024-10-01 ~ today**."
    ),
    args_schema=CompanyNewsParams,
    return_direct=False,
)
def a_share_company_news_tool(params_json: str) -> Dict[str, Any]:
    """
    Call this tool **after** `a_share_random_industry_picks_tool`.
    Pick one stock code from its `rows`, and pass it as:
      params_json = '{"symbol_or_name":"600519"}'  (or '{"symbol_or_name":"600519.SH"}')

    Output:
      {
        "symbol": "<the input code>",
        "rows": [
          {"published_at":"YYYY-MM-DD HH:MM:SS","title":"...","summary":"...","url":"...","source":"...","symbol":"600519","company_name":"..."},
          ...
        ],
        "vendor_meta": {"vendor":"eastmoney+sina+akshare","cached":false,"since":"2024-10-01","until":"YYYY-MM-DD"}
      }
    """
    params = _parse_json_params(params_json)
    return get_company_news_united(params)

# =========================
# 随机行业挑股：永久固定输入 "1"（保持不变）
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
