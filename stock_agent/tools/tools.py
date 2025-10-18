"""
from langchain_core.tools import StructuredTool


# Runnable --> BaseTool --> StructuredTool, Tool
#                       --> Custom Tool Classes

# tools定义示例
def search_function(query: str):
    return "LangChain"

search1 = StructuredTool.from_function(
    func=search_function,
    name="Search",
    description="useful for when you need to answer questions about current events"
)
"""

# ──────────────────────────────────────────────────────────────────────────────
# File: stock_agent/tools/tool_specs.py
# 极简版：用 StructuredTool.from_function 直接封装
# 依赖：pip install langchain-core
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

from typing import Optional, Dict, Any, List
from langchain_core.tools import StructuredTool

# 直接引用你已有的函数（已在 stock_agent.tools.__init__ 中导出）
from stock_agent.tools import (
    get_stock_market_data_united,
    get_company_news_united,
    list_a_share_industry_keywords,
    get_a_share_list_by_exact_industry,
)

# -----------------------
# 1) 行情工具（统一日线）
# -----------------------
def _a_share_market_data(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    adj: str = "qfq",
) -> Dict[str, Any]:
    """
    获取A股日线行情。参数：
    - symbol: 证券代码（如 '600519'/'600519.SH'/'sh600519'）
    - start_date/end_date: YYYY-MM-DD 或 YYYYMMDD，可留空
    - adj: 'qfq' 前复权 | 'hfq' 后复权 | 'none' 不复权
    """
    return get_stock_market_data_united(symbol, start_date, end_date, adj)

a_share_market_data = StructuredTool.from_function(
    func=_a_share_market_data,
    name="a_share_market_data",
    description="获取A股日线行情（支持前/后复权），统一字段输出。",
)

# -----------------------
# 2) 公司新闻工具（聚合）
# -----------------------
def _a_share_company_news(
    symbol_or_name: str,
    limit: int = 50,
    since: Optional[str] = None,
    until: Optional[str] = None,
) -> Dict[str, Any]:
    """
    聚合A股公司相关新闻（Eastmoney+Sina+AkShare）。参数：
    - symbol_or_name: 股票代码或公司名（如 '600519' 或 '贵州茅台'）
    - limit: 返回条数
    - since/until: 起止日期（YYYY-MM-DD 或 YYYYMMDD），可留空
    """
    return get_company_news_united(symbol_or_name, limit=limit, since=since, until=until)

a_share_company_news = StructuredTool.from_function(
    func=_a_share_company_news,
    name="a_share_company_news",
    description="聚合A股公司相关新闻（Eastmoney+Sina+AkShare 兜底），统一字段输出。",
)

# --------------------------------
# 3) 行业关键字清单（先列再选）
# --------------------------------
def _a_share_list_industries() -> Dict[str, Any]:
    """
    列出东财/AkShare提供的全部行业关键字（industry, code）。
    先调用本工具，让用户从清单里拷贝一个 industry 名字再调用下一个工具。
    """
    return list_a_share_industry_keywords()

a_share_list_industries = StructuredTool.from_function(
    func=_a_share_list_industries,
    name="a_share_list_industries",
    description="列出全部A股行业关键字（industry, code）。",
)

# ------------------------------------------------
# 4) 按精确行业名获取成分股（不做模糊，避免歧义）
# ------------------------------------------------
def _a_share_constituents_by_industry(
    industry_name: str,
    limit: int = 30,
    include_names: bool = False,
) -> Dict[str, Any]:
    """
    按精确行业名获取成分股（行业名需来自 a_share_list_industries 的 industry 字段）。
    - limit: 返回数量
    - include_names: True 则同时返回公司名称
    """
    return get_a_share_list_by_exact_industry(
        industry_name=industry_name,
        limit=limit,
        include_names=include_names,
    )

a_share_constituents_by_industry = StructuredTool.from_function(
    func=_a_share_constituents_by_industry,
    name="a_share_constituents_by_industry",
    description="按精确行业名（来自清单）获取成分股代码列表，可选返回名称。",
)

# 对外导出一个工具列表，Agent 直接拿去用即可
TOOLS: List[StructuredTool] = [
    a_share_market_data,
    a_share_company_news,
    a_share_list_industries,
    a_share_constituents_by_industry,
]


