# ──────────────────────────────────────────────────────────────────────────────
# File: stock_agent/tools/common.py
# ──────────────────────────────────────────────────────────────────────────────
import os
import re
import time
import json
import math
import queue
import typing as T
import datetime as dt
from dataclasses import dataclass

import pandas as pd


class ToolError(RuntimeError):
    pass


@dataclass
class RateLimiter:
    """Simple token-bucket rate limiter (process-local)."""

    rate: float = 5.0
    capacity: int = 10

    def __post_init__(self):
        self._tokens = float(self.capacity)
        self._ts = time.monotonic()

    def acquire(self, tokens: float = 1.0):
        while True:
            now = time.monotonic()
            elapsed = now - self._ts
            self._ts = now
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
            if self._tokens >= tokens:
                self._tokens -= tokens
                return
            missing = tokens - self._tokens
            time.sleep(max(0.001, missing / self.rate))


@dataclass
class ToolResultMeta:
    vendor: str
    latency_ms: int
    cached: bool
    effective_params: dict


def _ensure_date(d: T.Union[str, dt.date, dt.datetime, None]) -> T.Optional[str]:
    if d is None:
        return None
    if isinstance(d, dt.datetime):
        return d.strftime("%Y%m%d")
    if isinstance(d, dt.date):
        return d.strftime("%Y%m%d")
    s = str(d)
    if re.match(r"^\d{8}$", s):
        return s
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s.replace("-", "")
    raise ToolError(f"Invalid date format: {d}")


def _today_str_tz(tz: str = "Asia/Shanghai") -> str:
    # tz reserved for future tz-aware logic
    return dt.date.today().strftime("%Y%m%d")


# ---------------------------
# Stock symbol normalization
# ---------------------------

_AK_EX_MAP = {"SH": "sh", "SZ": "sz"}

def normalize_symbol(symbol: str) -> dict:
    """Normalize inputs like '600519', '600519.SH', 'SH600519'."""
    s = symbol.strip().upper()
    m = re.match(r"^(SH|SZ)?\s*0*(\d{6})(?:\.(SH|SZ))?$", s)
    if not m:
        m2 = re.match(r"^(\d{6})\.(SH|SZ)$", s)
        if not m2:
            raise ToolError(f"Unrecognized A股代码: {symbol}")
        pre, suf = m2.groups()
        code, ex = pre, suf
    else:
        left_ex, core, right_ex = m.groups()
        code = core
        ex = right_ex or left_ex
    if ex not in {"SH", "SZ", None}:
        raise ToolError(f"Unsupported exchange: {ex}")
    if ex is None:
        ex = "SH" if code.startswith("6") else "SZ"
    ts_code = f"{code}.{ex}"
    sina = f"{_AK_EX_MAP[ex]}{code}"
    return {"code": code, "exchange": ex, "ts_code": ts_code, "sina": sina}


def _lazy_import(name: str):
    try:
        module = __import__(name, fromlist=["*"])
        return module
    except Exception as e:
        raise ToolError(
            f"Missing optional dependency '{name}'. Please `pip install {name}`. Error: {e}"
        )


def with_retries(fn: T.Callable, tries: int = 3, delay: float = 0.8, backoff: float = 1.8):
    def _wrapped(*args, **kwargs):
        _tries, _delay = tries, delay
        last = None
        while _tries > 0:
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last = e
                _tries -= 1
                if _tries <= 0:
                    break
                time.sleep(_delay)
                _delay *= backoff
        raise ToolError(str(last))
    return _wrapped
