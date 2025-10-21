# ──────────────────────────────────────────────────────────────────────────────
# File: stock_agent/tools/unified_fundamentals.py
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

from typing import Optional, Dict, Any
import pandas as pd
import datetime as dt

from stock_agent.tools.common import (
    ToolError,
    RateLimiter,
    _lazy_import,
    with_retries,
)

# 统一列名的小工具
def _rename_like(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    rename = {}
    for cand, dst in mapping.items():
        cands = (cand,) if isinstance(cand, str) else list(cand)
        for c in cands:
            if c in df.columns:
                rename[c] = dst
                break
    return df.rename(columns=rename) if rename else df

def _ensure_latest_row(df: pd.DataFrame) -> pd.Series:
    # 尝试识别日期列
    for c in ["as_of", "日期", "报告期", "统计时间", "trade_date", "date", "报告日期"]:
        if c in df.columns:
            s = pd.to_datetime(df[c], errors="coerce")
            idx = s.idxmax()
            return df.loc[idx]
    # 没有日期列就取第一行
    return df.iloc[0]

def _to_float(v):
    try:
        return float(str(v).replace(",", "").replace("%", ""))
    except Exception:
        return None

class UnifiedFundamentalsTool:
    """
    A股统一基本面工具（优先 Eastmoney/同花顺接口，经由 AkShare）。
    输入：股票代码字符串（如 '600519' / '000001'）。
    输出：{'symbol', 'as_of', 'metrics': {...}, 'vendor_meta': {...}}
    """

    def __init__(self, rate_limit: Optional[RateLimiter] = None):
        # 放得更稳一些，避免被限
        self.rl = rate_limit or RateLimiter(rate=0.3, capacity=1)
        self._ak = None

    def _ensure_ak(self):
        if self._ak is None:
            self._ak = _lazy_import("akshare")
        return self._ak

    def _try_eastmoney_indicators(self, code: str) -> Optional[Dict[str, Any]]:
        """
        方案一：拉取综合指标（若接口存在）。
        常见列名做了多重兜底映射；仅取最新一行。
        """
        ak = self._ensure_ak()
        self.rl.acquire()
        # 一些环境里函数名可能不同；逐一尝试
        funcs = [
            getattr(ak, "stock_a_lg_indicator", None),               # 常见：综合指标（含PE/PB/ROE等）
            getattr(ak, "stock_a_indicator_lg", None),               # 变体命名
        ]
        for fn in funcs:
            if fn is None:
                continue
            try:
                df = with_retries(fn)(symbol=code)
            except TypeError:
                # 有些版本用 code= 或者不带命名参数
                try:
                    df = with_retries(fn)(code)
                except Exception:
                    continue
            except Exception:
                continue

            if df is None or df.empty:
                continue

            # 列名统一
            df = _rename_like(df, {
                ("市盈率TTM","PE(TTM)","市盈率-动态","pe_ttm"): "pe_ttm",
                ("市净率","PB","pb"): "pb",
                ("市销率TTM","PS(TTM)","ps_ttm"): "ps_ttm",
                ("净资产收益率TTM","ROE(TTM)","ROE"): "roe",
                ("毛利率","销售毛利率","毛利率(%)"): "gross_margin",
                ("营业总收入同比增长","营业收入同比增长","营收同比","营收同比增长率"): "revenue_yoy",
                ("净利润同比增长","归母净利润同比增长","净利润同比"): "net_profit_yoy",
                ("总市值","总市值(元)","总市值（元）","总市值-亿"): "market_cap",
                ("资产负债率","资产负债率(%)"): "debt_to_asset",
                ("报告期","统计时间","trade_date","日期","date"): "as_of",
            })

            row = _ensure_latest_row(df)
            as_of = row.get("as_of", dt.date.today())
            metrics = {
                "pe_ttm": _to_float(row.get("pe_ttm")),
                "pb": _to_float(row.get("pb")),
                "ps_ttm": _to_float(row.get("ps_ttm")),
                "roe": _to_float(row.get("roe")),
                "gross_margin": _to_float(row.get("gross_margin")),
                "revenue_yoy": _to_float(row.get("revenue_yoy")),
                "net_profit_yoy": _to_float(row.get("net_profit_yoy")),
                "market_cap": _to_float(row.get("market_cap")),
                "debt_to_asset": _to_float(row.get("debt_to_asset")),
            }
            return {
                "symbol": code,
                "as_of": pd.to_datetime(as_of, errors="coerce").strftime("%Y-%m-%d") if as_of else "",
                "metrics": {k: v for k, v in metrics.items() if v is not None},
                "vendor_meta": {"vendor": "akshare:eastmoney_indicators", "cached": False},
            }
        return None

    def _try_ths_abstract(self, code: str) -> Optional[Dict[str, Any]]:
        """
        方案二：同花顺财务摘要兜底（若存在）。
        """
        ak = self._ensure_ak()
        fn = getattr(ak, "stock_financial_abstract_ths", None)
        if fn is None:
            return None
        self.rl.acquire()
        try:
            df = with_retries(fn)(symbol=code)
        except Exception:
            return None
        if df is None or df.empty:
            return None

        df = _rename_like(df, {
            ("报告期","日期"): "as_of",
            ("净资产收益率","ROE"): "roe",
            ("毛利率","销售毛利率"): "gross_margin",
            ("净利润同比增长率","净利润同比增长"): "net_profit_yoy",
            ("营业收入同比增长率","营业收入同比增长"): "revenue_yoy",
            ("资产负债率",): "debt_to_asset",
        })
        row = _ensure_latest_row(df)
        as_of = row.get("as_of", dt.date.today())
        metrics = {
            "roe": _to_float(row.get("roe")),
            "gross_margin": _to_float(row.get("gross_margin")),
            "revenue_yoy": _to_float(row.get("revenue_yoy")),
            "net_profit_yoy": _to_float(row.get("net_profit_yoy")),
            "debt_to_asset": _to_float(row.get("debt_to_asset")),
        }
        return {
            "symbol": code,
            "as_of": pd.to_datetime(as_of, errors="coerce").strftime("%Y-%m-%d") if as_of else "",
            "metrics": {k: v for k, v in metrics.items() if v is not None},
            "vendor_meta": {"vendor": "akshare:ths_abstract", "cached": False},
        }

    # 对外主函数：只接受“股票代码”一个参数
    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        code = str(symbol).strip()
        if not code:
            raise ToolError("Empty or invalid input for stock code.")
        # 尝试 Eastmoney 综合指标
        out = self._try_eastmoney_indicators(code)
        if out:
            return out
        # 兜底：同花顺摘要
        out = self._try_ths_abstract(code)
        if out:
            return out
        # 全部失败
        raise ToolError(f"Failed to fetch fundamentals for {code} from available vendors.")

# 便捷函数（给 Tool 层和外部直接调用）
_DEF_FUND: Optional[UnifiedFundamentalsTool] = None

def get_a_share_fundamentals(symbol: str) -> Dict[str, Any]:
    global _DEF_FUND
    if _DEF_FUND is None:
        _DEF_FUND = UnifiedFundamentalsTool()
    return _DEF_FUND.get_fundamentals(symbol)
