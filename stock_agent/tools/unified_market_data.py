# ──────────────────────────────────────────────────────────────────────────────
# File: stock_agent/tools/unified_market_data.py
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

from typing import Optional, List, Literal
import typing as T
import os
import time
import datetime as dt

import pandas as pd

from stock_agent.tools.common import (
    ToolError,
    ToolResultMeta,
    RateLimiter,
    _ensure_date,
    _today_str_tz,
    normalize_symbol,
    _lazy_import,
    with_retries,
)

class UnifiedMarketDataTool:
    """A股统一行情工具（优先 TuShare，其次 AkShare）。

    输出字段（DataFrame）:
    date, open, high, low, close, volume, amount, adj_factor
    """

    def __init__(
        self,
        tushare_token: Optional[str] = None,
        prefer: Optional[List[str]] = None,
        rate_limit: Optional[RateLimiter] = None,
    ):
        self.tushare_token = tushare_token or os.environ.get("TUSHARE_TOKEN")
        # 若未给 prefer：有 token 则 tushare 优先，否则 akshare 优先
        self.prefer = prefer or (["tushare", "akshare"] if self.tushare_token else ["akshare", "tushare"])
        self.rl = rate_limit or RateLimiter(rate=4, capacity=8)
        self._ts = None  # TuShare client
        self._ak = None  # AkShare module

    # ---------------------------
    # Public
    # ---------------------------
    def get_kline_daily(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adj: Optional[Literal["qfq", "hfq", "none"]] = "qfq",
    ) -> pd.DataFrame:
        """主入口：按日K获取行情（自动按 prefer 在多供应商间回退）"""
        sym = normalize_symbol(symbol)
        start = _ensure_date(start_date)
        end = _ensure_date(end_date) or _today_str_tz()
        today = _today_str_tz()
        if end > today:
            end = today

        last_err = None
        for vendor in self.prefer:
            t0 = time.time()
            try:
                if vendor == "tushare":
                    df = self._get_kline_tushare(sym, start, end, adj)
                elif vendor == "akshare":
                    df = self._get_kline_akshare(sym, start, end, adj)
                else:
                    continue
                latency = int((time.time() - t0) * 1000)
                df.attrs["vendor_meta"] = ToolResultMeta(
                    vendor=vendor,
                    latency_ms=latency,
                    cached=False,
                    effective_params={"start": start, "end": end, "adj": adj},
                ).__dict__
                return df
            except Exception as e:
                last_err = e
                continue
        raise ToolError(f"All vendors failed for {symbol}: {last_err}")

    # ---------------------------
    # Vendors
    # ---------------------------
    def _ensure_ts(self):
        if self._ts is None:
            if not self.tushare_token:
                raise ToolError("TuShare token missing. Set TUSHARE_TOKEN or pass tushare_token.")
            ts = _lazy_import("tushare")
            ts.set_token(self.tushare_token)
            self._ts = ts.pro_api()
        return self._ts

    def _ensure_ak(self):
        if self._ak is None:
            self._ak = _lazy_import("akshare")
        return self._ak

    def _get_kline_tushare(self, sym: dict, start: Optional[str], end: str, adj: Optional[str]) -> pd.DataFrame:
        pro = self._ensure_ts()
        self.rl.acquire()
        params = {"ts_code": sym["ts_code"], "start_date": start, "end_date": end}
        df = with_retries(pro.daily)(**{k: v for k, v in params.items() if v})
        if df is None or df.empty:
            raise ToolError("TuShare.daily returned empty.")
        df.rename(
            columns={
                "trade_date": "date",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "vol": "volume",
                "amount": "amount",
            },
            inplace=True,
        )
        df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
        df.sort_values("date", inplace=True)
        df = df[["date", "open", "high", "low", "close", "volume", "amount"]]

        if adj and adj != "none":
            af = with_retries(pro.adj_factor)(ts_code=sym["ts_code"], start_date=start, end_date=end)
            if af is not None and not af.empty:
                af.rename(columns={"trade_date": "date"}, inplace=True)
                af["date"] = pd.to_datetime(af["date"], format="%Y%m%d")
                af.sort_values("date", inplace=True)
                df = df.merge(af[["date", "adj_factor"]], on="date", how="left")
                # 价格复权
                if adj == "qfq":
                    base = df["adj_factor"].iloc[-1]
                else:  # hfq
                    base = df["adj_factor"].iloc[0]
                scale = df["adj_factor"] / base
                for col in ["open", "high", "low", "close"]:
                    df[col] = (df[col] / scale).astype(float)
            else:
                df["adj_factor"] = pd.NA
        else:
            df["adj_factor"] = pd.NA
        return df

    def _get_kline_akshare(self, sym: dict, start: Optional[str], end: str, adj: Optional[str]) -> pd.DataFrame:
        ak = self._ensure_ak()
        self.rl.acquire()
        period = "daily"
        adjust = None if (adj is None or adj == "none") else adj
        df = with_retries(ak.stock_zh_a_hist)(
            symbol=sym["code"], start_date=start, end_date=end, period=period, adjust=adjust
        )
        if df is None or df.empty:
            raise ToolError("AkShare.stock_zh_a_hist returned empty.")
        rename_map = {
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
        }
        for k, v in rename_map.items():
            if k in df.columns:
                df.rename(columns={k: v}, inplace=True)
        df["date"] = pd.to_datetime(df["date"])
        df = df[["date", "open", "high", "low", "close", "volume", "amount"]]
        df["adj_factor"] = pd.NA
        return df


# =========================
# 单字典参数的便捷入口（兼容旧调用）
# =========================
_DEF_TOOL: Optional[UnifiedMarketDataTool] = None

def _coerce_params_dict(
    params: Optional[T.Union[dict, str]] = None,
    **kwargs,
) -> dict:
    """
    将各种输入形式统一成 dict：
    - params 为 dict：直接解析其中字段
    - params 为 str：视为 symbol
    - 兼容旧式 kwargs：symbol=..., start_date=..., end_date=..., adj=..., prefer=..., tushare_token=...
    """
    if params is None:
        params = {}
    if isinstance(params, str):
        params = {"symbol": params}
    if not isinstance(params, dict):
        raise ToolError("params must be a dict or a symbol string")

    # 合并 kwargs（kwargs 优先）
    merged = {**params, **kwargs}

    # 规范化键名（可加别名）
    symbol = merged.get("symbol") or merged.get("ts_code") or merged.get("ticker")
    if not symbol:
        raise ToolError("`symbol` is required in params dict")

    start_date = merged.get("start_date")
    end_date = merged.get("end_date")
    adj = merged.get("adj", "qfq")
    prefer = merged.get("prefer")  # Optional[List[str]]
    tushare_token = merged.get("tushare_token") or os.environ.get("TUSHARE_TOKEN")

    # 合法性
    if adj not in (None, "qfq", "hfq", "none"):
        raise ToolError("`adj` must be one of: 'qfq' | 'hfq' | 'none'")

    return {
        "symbol": str(symbol),
        "start_date": start_date,
        "end_date": end_date,
        "adj": adj,
        "prefer": prefer,
        "tushare_token": tushare_token,
    }

def get_stock_market_data_united(
    params: Optional[T.Union[dict, str]] = None,
    **kwargs,
) -> T.Dict[str, T.Any]:
    """
    单参数（dict）入口 —— 适配只能传一个参数给 Agent 的场景。

    参数字典 schema（全部可选，symbol 必填）：
    {
      "symbol": "600519.SH" | "600519",          # 必填；支持含交易所或纯 6 位
      "start_date": "YYYY-MM-DD" | "YYYYMMDD",   # 选填
      "end_date":   "YYYY-MM-DD" | "YYYYMMDD",   # 选填；默认今天
      "adj": "qfq" | "hfq" | "none",             # 选填；默认 "qfq"
      "prefer": ["akshare","tushare"],           # 选填；供应商优先级
      "tushare_token": "<YOUR_TUSHARE_TOKEN>"    # 选填；如未设置环境变量
    }

    兼容旧式调用：get_stock_market_data_united(symbol="600519.SH", start_date="2025-01-01", ...)
    """
    p = _coerce_params_dict(params, **kwargs)

    global _DEF_TOOL
    # 若首次调用或需要更换 token，则重建 Tool；否则复用并允许动态修改 prefer
    need_recreate = (_DEF_TOOL is None) or (p["tushare_token"] and p["tushare_token"] != _DEF_TOOL.tushare_token)
    if need_recreate:
        _DEF_TOOL = UnifiedMarketDataTool(
            tushare_token=p["tushare_token"],
            prefer=p["prefer"],
        )
    else:
        if p["prefer"]:
            _DEF_TOOL.prefer = p["prefer"]

    df = _DEF_TOOL.get_kline_daily(
        symbol=p["symbol"],
        start_date=p["start_date"],
        end_date=p["end_date"],
        adj=p["adj"],
    )
    meta = df.attrs.get("vendor_meta", {})
    out = df.copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return {
        "symbol": p["symbol"],
        "rows": out.to_dict(orient="records"),
        "vendor_meta": meta,
    }

