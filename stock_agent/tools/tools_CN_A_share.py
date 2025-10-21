# ──────────────────────────────────────────────────────────────────────────────
# File: stock_agent/tools/tools_CN_A_share.py
# LangChain @tool decorator + Pydantic args_schema (with descriptions)
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain.tools import tool
import json

# Reuse business functions already exported in your package
from stock_agent.tools import (
    get_stock_market_data_united,
    get_company_news_united,
    get_random_a_share_sequence,   # zero-arg function (fixed internal logic)
)

# =========================
# Market data & news: JSON-string params (descriptions updated to English)
# =========================

def _parse_json_params(params_json: str) -> Dict[str, Any]:
    try:
        data = json.loads(params_json)
    except Exception as e:
        raise ValueError(f"params_json is not valid JSON: {e}")
    if not isinstance(data, dict):
        raise ValueError('params_json must be a JSON object (e.g. {"key":"value"}).')
    return data

def _coerce_symbol_from_input(params_json: str, key_candidates=("symbol", "symbol_or_name", "code")) -> str:
    """
    支持以下输入形态：
      1) 裸字符串: "688498"
      2) JSON 对象字符串: '{"symbol":"688498"}' / '{"symbol_or_name":"688498"}'
      3) JSON 纯量: "301048"（会被 json 解析成数字 301048）
      4) JSON 列表: '["600519"]'（取第一个）
    统一返回: 股票代码字符串
    """
    s = "" if params_json is None else str(params_json).strip()
    if not s:
        raise ValueError("Empty or invalid input for stock code.")

    # 先尝试按 JSON 解析
    try:
        obj = json.loads(s)
    except Exception:
        # 不是 JSON，就按原始字符串处理
        return s

    # 解析后是字典：从候选键中取值
    if isinstance(obj, dict):
        for k in key_candidates:
            if k in obj and obj[k]:
                return str(obj[k]).strip()
        raise ValueError(f"Missing one of keys {key_candidates} in JSON object.")

    # 解析后是字符串/数字：直接转成字符串返回
    if isinstance(obj, (str, int, float)):
        return str(obj).strip()

    # 解析后是列表：取第一个元素
    if isinstance(obj, list) and obj:
        return str(obj[0]).strip()

    # 其它类型，退回原始字符串
    return s



class MarketDataParams(BaseModel):
    params_json: str = Field(
        ...,
        description="Use after a_share_random_industry_picks; provide one A-share code from its output, e.g., '600159'.",
    )

class CompanyNewsParams(BaseModel):
    params_json: str = Field(
        ...,
        description="Use after a_share_random_industry_picks; provide one A-share code from its output, e.g., '600159'.",
    )

@tool(
    name_or_callable="a_share_market_data",
    description="Use after a_share_random_industry_picks; retrieve recent market data for that stock.",
    args_schema=MarketDataParams,
    return_direct=False,
)
def a_share_market_data_tool(params_json: str) -> Dict[str, Any]:
    # 兼容裸字符串 & JSON 对象字符串
    symbol = _coerce_symbol_from_input(params_json, key_candidates=("symbol", "code"))
    # 你的底层函数现在只接受“代码字符串”
    return get_stock_market_data_united(symbol)

# —— 修改新闻工具：提取代码字符串后调用底层“仅代码”版本 —— #
@tool(
    name_or_callable="a_share_company_news",
    description="Use after a_share_random_industry_picks; retrieve recent news for that stock.",
    args_schema=CompanyNewsParams,
    return_direct=False,
)
def a_share_company_news_tool(params_json: str) -> Dict[str, Any]:
    # 兼容裸字符串 & JSON 对象字符串
    symbol = _coerce_symbol_from_input(params_json, key_candidates=("symbol_or_name", "symbol", "code"))
    # 你的底层函数现在只接受“代码字符串”
    return get_company_news_united(symbol)

# =========================
# Random industry picks: permanently fixed input "1" (unchanged)
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
    # Ignore 'one'; always execute fixed logic
    return get_random_a_share_sequence()

# # Export tools list if needed
# TOOLS: List[Any] = [
#     a_share_market_data_tool,
#     a_share_company_news_tool,
#     a_share_random_industry_picks_tool,
# ]
