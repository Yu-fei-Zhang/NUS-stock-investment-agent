# ──────────────────────────────────────────────────────────────────────────────
# File: stock_agent/tools/unified_fundamentals.py
# Unified A-share fundamentals: stable vendors, minimal params (symbol only)
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

from typing import Optional, Dict, Any, List
import datetime as dt
import pandas as pd
import requests

from stock_agent.tools.common import (
    ToolError,
    RateLimiter,
    _lazy_import,
    with_retries,
)

# ----------------------------
# 小工具
# ----------------------------
def _to_float(v) -> Optional[float]:
    if v is None:
        return None
    try:
        s = str(v).replace(",", "").replace("%", "").strip()
        if s in {"", "-", "nan", "None"}:
            return None
        return float(s)
    except Exception:
        return None


def _to_prefixed(code: str) -> str:
    """把 6/5/9 开头视为上交所，其他视为深交所，转为东财 PC_HSF10 需要的 SH/SZ 前缀"""
    code = str(code).strip()
    if not code:
        return code
    if code[0] in {"5", "6", "9"}:
        return f"SH{code}"
    return f"SZ{code}"


def _pick_first(d: Dict[str, Any], candidates: List[str]) -> Optional[float]:
    """在 dict 中按候选键顺序取第一个非空值，并转为 float"""
    for k in candidates:
        if k in d and d[k] not in (None, "", "-", "—"):
            val = _to_float(d[k])
            if val is not None:
                return val
    return None


def _latest_by_date(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """从多期财务数据里挑最近一期（按常见日期字段最大）"""
    if not rows:
        return {}
    def _dt(x: Dict[str, Any]):
        for k in ("reportdate", "endDate", "date", "报告期", "报告日期"):
            if k in x:
                try:
                    return pd.to_datetime(x[k], errors="coerce")
                except Exception:
                    pass
        return pd.NaT
    return max(rows, key=_dt)


# ----------------------------
# 主工具
# ----------------------------
class UnifiedFundamentalsTool:
    """
    A股统一基本面工具（优先稳定路径；仅需股票代码一个参数）。

    输入:  symbol (str) 例如 '600519', '000001'
    输出:  {
             "symbol": "...",
             "as_of": "YYYY-MM-DD",
             "metrics": {
               "price": float,              # 最新价（若可得）
               "total_shares": float,       # 总股本（股）
               "float_shares": float,       # 流通股（股）
               "market_cap": float,         # 市值（元）= 价格 * 总股本
               "eps": float,                # 每股收益（TTM/最新期）
               "bps": float,                # 每股净资产
               "pe_ttm": float,             # 估算：price / eps
               "pb": float,                 # 估算：price / bps
               "roe": float,                # ROE（TTM/最新期）
               "gross_margin": float,       # 毛利率（%）
               "revenue_yoy": float,        # 营收同比（%）
               "net_profit_yoy": float,     # 净利同比（%）
               "debt_to_asset": float,      # 资产负债率（%）
             },
             "vendor_meta": {"vendor": "...", "cached": False}
           }
    """

    def __init__(self, rate_limit: Optional[RateLimiter] = None):
        # 严一点的限流，避免被风控
        self.rl = rate_limit or RateLimiter(rate=0.3, capacity=1)
        self._ak = None

    # ---- 基础设施 ----
    def _ensure_ak(self):
        if self._ak is None:
            self._ak = _lazy_import("akshare")
        return self._ak

    # ---- 供应商 1：个股信息（稳定） => 价格/股本/市值 ----
    def _try_individual_info(self, code: str) -> Optional[Dict[str, Any]]:
        """
        ak.stock_individual_info_em(symbol=code)
        常见列：['item','value']，含 '最新'，'总股本'，'流通股' 等。
        """
        ak = self._ensure_ak()
        fn = getattr(ak, "stock_individual_info_em", None)
        if fn is None:
            return None
        self.rl.acquire()
        try:
            df = with_retries(fn)(symbol=code)
        except Exception:
            return None
        if df is None or df.empty or "item" not in df.columns or "value" not in df.columns:
            return None

        kv = {str(r["item"]).strip(): r["value"] for _, r in df.iterrows()}
        price = _to_float(kv.get("最新"))
        total_shares = _to_float(kv.get("总股本"))
        float_shares = _to_float(kv.get("流通股"))

        metrics = {}
        if price is not None:
            metrics["price"] = price
        if total_shares is not None:
            metrics["total_shares"] = total_shares
        if float_shares is not None:
            metrics["float_shares"] = float_shares
        if price is not None and total_shares is not None:
            metrics["market_cap"] = price * total_shares

        if not metrics:
            return None

        return {
            "symbol": code,
            "as_of": dt.date.today().strftime("%Y-%m-%d"),
            "metrics": metrics,
            "vendor_meta": {"vendor": "akshare:individual_info_em", "cached": False},
        }

    # ---- 供应商 2：东财 PC_HSF10 财务指标（可用 JSON） => EPS/BPS/ROE/增速等 ----
    def _try_hsf10_finance_indicator(self, code: str) -> Optional[Dict[str, Any]]:
        """
        访问： https://emweb.securities.eastmoney.com/PC_HSF10/FinanceAnalysis/FinanceIndicator?code=SH600519
        返回 JSON，取最近一期，提取 EPS/BPS/ROE/营收&净利同比/毛利率。
        """
        self.rl.acquire()
        em_code = _to_prefixed(code)
        url = (
            "https://emweb.securities.eastmoney.com/PC_HSF10/FinanceAnalysis/FinanceIndicator"
            f"?code={em_code}"
        )
        try:
            r = requests.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/124.0 Safari/537.36"
                },
                timeout=12,
            )
            if r.status_code != 200:
                return None
            j = r.json()
        except Exception:
            return None

        rows = j.get("data") or j.get("Data") or j.get("result") or j.get("Result") or []
        if not isinstance(rows, list) or not rows:
            return None

        row = _latest_by_date(rows)
        if not row:
            return None

        eps = _pick_first(row, ["basicEPS", "EPS", "eps", "jbmgsy", "EPSJB"])
        bps = _pick_first(row, ["bps", "BPS", "mgjzc"])
        roe = _pick_first(row, ["roeAvg", "ROEAVG", "roe", "jzcsyl"])
        revenue_yoy = _pick_first(row, ["revenueGrowRate", "YSTBZ", "yysrzzl"])
        net_profit_yoy = _pick_first(row, ["netProfitGrowRate", "JLRBZ", "netprofitgrowth"])
        gross_margin = _pick_first(row, ["grossprofitmargin", "XSMLL"])

        as_of = None
        for k in ("reportdate", "endDate", "date", "报告期", "报告日期"):
            if k in row:
                as_of = row[k]
                break

        metrics = {
            k: v for k, v in {
                "eps": eps,
                "bps": bps,
                "roe": roe,
                "revenue_yoy": revenue_yoy,
                "net_profit_yoy": net_profit_yoy,
                "gross_margin": gross_margin,
            }.items() if v is not None
        }
        if not metrics:
            return None

        return {
            "symbol": code,
            "as_of": pd.to_datetime(as_of, errors="coerce").strftime("%Y-%m-%d") if as_of else "",
            "metrics": metrics,
            "vendor_meta": {"vendor": "eastmoney:hsf10_finance_indicator", "cached": False},
        }

    # ---- 供应商 3：同花顺摘要（AkShare） => 兜底补数 ----
    def _try_ths_abstract(self, code: str) -> Optional[Dict[str, Any]]:
        """
        ak.stock_financial_abstract_ths(symbol=code)
        常能取到 ROE / 毛利率 / 收入&净利同比 / 资产负债率
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

        # 列名软映射
        def _rename_like(df_: pd.DataFrame, mapping: dict) -> pd.DataFrame:
            rename = {}
            for cand, dst in mapping.items():
                cands = (cand,) if isinstance(cand, str) else list(cand)
                for c in cands:
                    if c in df_.columns:
                        rename[c] = dst
                        break
            return df_.rename(columns=rename) if rename else df_

        df = _rename_like(df, {
            ("报告期", "日期"): "as_of",
            ("净资产收益率", "ROE"): "roe",
            ("毛利率", "销售毛利率"): "gross_margin",
            ("净利润同比增长率", "净利润同比增长"): "net_profit_yoy",
            ("营业收入同比增长率", "营业收入同比增长"): "revenue_yoy",
            ("资产负债率",): "debt_to_asset",
        })

        # 取最近一期
        def _latest_row(d: pd.DataFrame) -> pd.Series:
            if "as_of" in d.columns:
                s = pd.to_datetime(d["as_of"], errors="coerce")
                idx = s.idxmax()
                return d.loc[idx]
            return d.iloc[0]

        row = _latest_row(df)
        as_of = row.get("as_of")

        metrics = {
            "roe": _to_float(row.get("roe")),
            "gross_margin": _to_float(row.get("gross_margin")),
            "revenue_yoy": _to_float(row.get("revenue_yoy")),
            "net_profit_yoy": _to_float(row.get("net_profit_yoy")),
            "debt_to_asset": _to_float(row.get("debt_to_asset")),
        }
        metrics = {k: v for k, v in metrics.items() if v is not None}
        if not metrics:
            return None

        return {
            "symbol": code,
            "as_of": pd.to_datetime(as_of, errors="coerce").strftime("%Y-%m-%d") if as_of else "",
            "metrics": metrics,
            "vendor_meta": {"vendor": "akshare:ths_abstract", "cached": False},
        }

    # ---- 对外主函数：只接受“股票代码”一个参数 ----
    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        code = str(symbol).strip()
        if not code:
            raise ToolError("Empty or invalid input for stock code.")

        merged: Dict[str, Any] = {}
        as_of = ""

        # A) 个股信息：价格/股本/市值（稳定）
        out_info = self._try_individual_info(code)
        if out_info:
            merged.update({k: v for k, v in out_info["metrics"].items() if v is not None})
            as_of = as_of or out_info.get("as_of", "")

        # B) 东财 PC_HSF10：EPS/BPS/ROE/增速等
        out_hsf10 = self._try_hsf10_finance_indicator(code)
        if out_hsf10:
            merged.update({k: v for k, v in out_hsf10["metrics"].items() if v is not None})
            as_of = as_of or out_hsf10.get("as_of", "")

        # C) 同花顺摘要兜底
        out_ths = self._try_ths_abstract(code)
        if out_ths:
            merged.update({k: v for k, v in out_ths["metrics"].items() if v is not None})
            as_of = as_of or out_ths.get("as_of", "")

        # D) 本地估算 PB / PE（有 price + bps/eps 才计算）
        price = merged.get("price")
        bps = merged.get("bps")
        eps = merged.get("eps")
        if price is not None and bps and bps > 0:
            merged["pb"] = price / bps
        if price is not None and eps and eps > 0:
            merged["pe_ttm"] = price / eps

        if not merged:
            raise ToolError(f"Failed to fetch fundamentals for {code} from available vendors.")

        vendors = []
        for v in (out_info, out_hsf10, out_ths):
            if v:
                vendors.append(v["vendor_meta"]["vendor"])

        return {
            "symbol": code,
            "as_of": as_of or dt.date.today().strftime("%Y-%m-%d"),
            "metrics": merged,
            "vendor_meta": {"vendor": "+".join(vendors), "cached": False},
        }


# ----------------------------
# 便捷函数（供外部/Tool层直接调用）
# ----------------------------
_DEF_FUND: Optional[UnifiedFundamentalsTool] = None

def get_a_share_fundamentals(symbol: str) -> Dict[str, Any]:
    global _DEF_FUND
    if _DEF_FUND is None:
        _DEF_FUND = UnifiedFundamentalsTool()
    return _DEF_FUND.get_fundamentals(symbol)
