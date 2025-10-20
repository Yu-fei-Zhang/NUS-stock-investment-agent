# ──────────────────────────────────────────────────────────────────────────────
# File: stock_agent/tools/unified_market_data.py
# ──────────────────────────────────────────────────────────────────────────────
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
        prefer: List[str] = None,
        rate_limit: Optional[RateLimiter] = None,
    ):
        self.tushare_token = tushare_token or os.environ.get("TUSHARE_TOKEN")
        # 有 token 则优先 tushare；否则 akshare
        self.prefer = prefer or (["tushare", "akshare"] if self.tushare_token else ["akshare", "tushare"])
        self.rl = rate_limit or RateLimiter(rate=4, capacity=8)
        self._ts = None  # TuShare client
        self._ak = None  # AkShare module

    def get_kline_daily(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adj: Optional[Literal["qfq", "hfq", "none"]] = "qfq",
    ) -> pd.DataFrame:
        sym = normalize_symbol(symbol)
        start = _ensure_date(start_date) if start_date else None
        end = _ensure_date(end_date) if end_date else _today_str_tz()
        today = _today_str_tz()
        if end > today:
            end = today

        # 若未给 start_date，这里兜底取近两周（含今天，向前 14 天）
        if not start:
            # _today_str_tz -> "YYYYMMDD"
            tdate = dt.datetime.strptime(today, "%Y%m%d").date()
            start = (tdate - dt.timedelta(days=14)).strftime("%Y%m%d")

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
                if adj == "qfq":
                    base = df["adj_factor"].iloc[-1]
                    scale = df["adj_factor"] / base
                else:
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


# Convenience function for tool-calling
_DEF_TOOL: Optional[UnifiedMarketDataTool] = None

def get_stock_market_data_united(symbol: str) -> T.Dict[str, T.Any]:
    """
    便捷入口：只传一支股票代码，日期窗口默认取**近两周**（含今天）。
    - 示例：get_stock_market_data_united("600519.SH") 或 "600519"
    - 价格复权模式固定为 'qfq'（可在类接口中自定义）

    返回 JSON:
    {
      "symbol": "<输入的代码>",
      "rows": [
        {"date":"YYYY-MM-DD","open":...,"high":...,"low":...,"close":...,"volume":...,"amount":...,"adj_factor":...},
        ...
      ],
      "vendor_meta": {...}
    }
    """
    global _DEF_TOOL
    if _DEF_TOOL is None:
        _DEF_TOOL = UnifiedMarketDataTool()

    # 计算默认窗口：今日 & 今日-14天
    end_ymd = _today_str_tz()  # "YYYYMMDD"
    end_date = end_ymd
    start_date = (dt.datetime.strptime(end_ymd, "%Y%m%d").date() - dt.timedelta(days=14)).strftime("%Y%m%d")

    # 固定 qfq（如需开放，可改为参数或环境变量控制）
    df = _DEF_TOOL.get_kline_daily(symbol, start_date=start_date, end_date=end_date, adj="qfq")

    meta = df.attrs.get("vendor_meta", {})
    out = df.copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return {"symbol": symbol, "rows": out.to_dict(orient="records"), "vendor_meta": meta}
