# ──────────────────────────────────────────────────────────────────────────────
# File: stock_agent/tools/unified_news.py
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

from typing import Optional, List, Dict
import typing as T
import math
import datetime as dt

import pandas as pd

from stock_agent.tools.common import (
    ToolError,
    RateLimiter,
    _ensure_date,
    normalize_symbol,
    _lazy_import,
    with_retries,
)


class UnifiedNewsTool:
    """
    A股统一新闻工具（Eastmoney + Sina + AkShare 兜底）

    统一输出字段（DataFrame）:
      - published_at: pd.Timestamp（Asia/Shanghai，本地无 tz）
      - title: str
      - summary: str | None
      - url: str
      - source: "eastmoney" | "sina" | "akshare"
      - symbol: str（代码或查询关键字）
      - company_name: str
    """

    def __init__(self, rate_limit: Optional[RateLimiter] = None):
        self.rl = rate_limit or RateLimiter(rate=3, capacity=6)
        self._ak = None

    def _ensure_ak(self):
        if self._ak is None:
            self._ak = _lazy_import("akshare")
        return self._ak

    # ---------------------------
    # Helpers
    # ---------------------------
    def _code_to_name(self, code: str) -> Optional[str]:
        ak = self._ensure_ak()
        self.rl.acquire()
        df = with_retries(ak.stock_info_a_code_name)()
        if df is None or df.empty:
            return None
        df = df.rename(columns={"code": "code", "name": "name"})
        row = df[df["code"] == code]
        if not row.empty:
            return row.iloc[0]["name"]
        return None

    # ---------------------------
    # Vendors
    # ---------------------------
    def _fetch_eastmoney_search(self, keyword: str, limit: int = 50) -> pd.DataFrame:
        """
        抓取东财搜索页（HTML），适配多入口与 DOM 变化。
        """
        try:
            import requests
            from bs4 import BeautifulSoup
        except Exception:
            return pd.DataFrame()

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://www.eastmoney.com/",
        }

        # 同时尝试两种路径与两种参数名
        url_candidates = [
            ("https://so.eastmoney.com/news/s", "keyword"),
            ("https://so.eastmoney.com/news/s", "KeyWord"),
            ("https://so.eastmoney.com/web/s",  "keyword"),
            ("https://so.eastmoney.com/web/s",  "KeyWord"),
        ]

        items: List[Dict[str, T.Any]] = []
        for base, keyname in url_candidates:
            if len(items) >= limit:
                break
            self.rl.acquire()

            def _get_html():
                r = requests.get(base, params={keyname: keyword}, headers=headers, timeout=10)
                r.encoding = r.apparent_encoding or "utf-8"
                return r.text

            html = with_retries(_get_html)()
            soup = BeautifulSoup(html, "lxml")

            # 常见几种标题/时间/摘要结构
            anchors = []
            anchors += soup.select(".news-item h3 a, .title a")
            anchors += soup.select("ul#newsList li h3 a, ul.search-list li h3 a")
            anchors += soup.select("div.news-item a[href^='http']")
            seen = set()
            for a in anchors:
                href = a.get("href")
                title = a.get_text(strip=True)
                if not href or not title:
                    continue
                key = (title, href)
                if key in seen:
                    continue
                seen.add(key)

                parent = a.find_parent(".news-item") or a.find_parent("li") or a.parent
                pub, summ = None, None
                if parent:
                    tnode = parent.select_one(".time, .date, time, span.time")
                    if tnode:
                        pub = tnode.get_text(strip=True)
                    sn = parent.select_one("p, .desc, .summary")
                    if sn:
                        summ = sn.get_text(strip=True)

                items.append(
                    {
                        "published_at": pub,
                        "title": title,
                        "summary": summ,
                        "url": href,
                        "source": "eastmoney",
                    }
                )
                if len(items) >= limit:
                    break

        df = pd.DataFrame(items)
        if not df.empty and "published_at" in df:
            def _parse_dt(s):
                if not s:
                    return pd.NaT
                for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%m-%d %H:%M"):
                    try:
                        d = dt.datetime.strptime(s, fmt)
                        if fmt == "%m-%d %H:%M":
                            d = d.replace(year=dt.date.today().year)
                        return d
                    except Exception:
                        continue
                return pd.NaT
            df["published_at"] = df["published_at"].apply(_parse_dt)
        return df

    def _fetch_sina_stock_news(self, sina_symbol: str, pages: int = 2) -> pd.DataFrame:
        """
        抓取新浪个股新闻分页（HTML）。注意 GBK/GB2312 编码！
        """
        try:
            import requests
            from bs4 import BeautifulSoup
        except Exception:
            return pd.DataFrame()

        items: List[Dict[str, T.Any]] = []
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://finance.sina.com.cn/",
        }

        for p in range(1, pages + 1):
            self.rl.acquire()
            url = "https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllNewsStock.php"
            params = {"symbol": sina_symbol, "Page": p}

            def _get_text():
                r = requests.get(url, params=params, headers=headers, timeout=10)
                # 明确按 GB 编码解码（多数页 headers 没写或写错）
                r.encoding = "gb18030"
                return r.text

            html = with_retries(_get_text)()
            soup = BeautifulSoup(html, "lxml")

            # 多种 DOM 兜底
            candidates = []
            candidates += soup.select("#newslist a[target='_blank']")               # 旧结构
            candidates += soup.select("div.datelist a[target='_blank']")            # 常见结构
            candidates += soup.select("ul#newslist2 li a[target='_blank']")         # 变体
            seen = set()
            for a in candidates:
                href = a.get("href")
                title = a.get_text(strip=True)
                if not href or not title:
                    continue
                key = (title, href)
                if key in seen:
                    continue
                seen.add(key)
                # 时间节点常在兄弟/父节点
                pub = None
                sib = a.find_next_sibling("span") or a.parent.find("span")
                if sib:
                    pub = sib.get_text(strip=True).strip("[]（）()")
                items.append(
                    {
                        "published_at": pub,
                        "title": title,
                        "summary": None,
                        "url": href,
                        "source": "sina",
                    }
                )

        df = pd.DataFrame(items)
        if not df.empty and "published_at" in df:
            def _parse(s):
                if not s:
                    return pd.NaT
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                    try:
                        return dt.datetime.strptime(s, fmt)
                    except Exception:
                        continue
                return pd.NaT
            df["published_at"] = df["published_at"].apply(_parse)
        return df

    def _fetch_akshare_general_news(self, keyword: str, limit: int = 50) -> pd.DataFrame:
        """
        使用 AkShare 通用财经新闻接口，按关键词过滤标题。
        """
        ak = self._ensure_ak()
        self.rl.acquire()
        try:
            df = with_retries(ak.stock_news_em)()
        except Exception:
            return pd.DataFrame()

        if df is None or df.empty:
            return pd.DataFrame()

        # 统一字段名
        rename = {}
        for c in df.columns:
            if c in ("标题", "title"):
                rename[c] = "title"
            elif c in ("摘要", "content", "summary"):
                rename[c] = "summary"
            elif c in ("链接", "url"):
                rename[c] = "url"
            elif c in ("时间", "发布时间", "publish_time"):
                rename[c] = "published_at"
        if rename:
            df = df.rename(columns=rename)

        if "title" not in df:
            return pd.DataFrame()

        m = df["title"].astype(str).str.contains(keyword, case=False, na=False)
        df = df[m].copy()
        df["source"] = "akshare"
        if "published_at" in df:
            df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")

        return df.head(limit)

    # ---------------------------
    # Public API
    # ---------------------------
    def get_company_news(
        self,
        symbol_or_name: str,
        limit: int = 50,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> pd.DataFrame:
        # 解析为代码/公司名；若传入公司名则直接用作 keyword
        try:
            sym = normalize_symbol(symbol_or_name)
            code = sym["code"]
            name = self._code_to_name(code) or code
            sina_symbol = sym["sina"]
        except ToolError:
            code = None
            name = symbol_or_name.strip()
            sina_symbol = None

        frames: List[pd.DataFrame] = []

        # 1) 东财：公司名关键词搜索
        try:
            frames.append(self._fetch_eastmoney_search(name, limit=limit))
        except Exception:
            pass

        # 2) 新浪：如果传了代码，使用个股新闻分页
        if sina_symbol:
            try:
                pages = max(1, min(3, int(math.ceil(limit / 30))))
                frames.append(self._fetch_sina_stock_news(sina_symbol, pages=pages))
            except Exception:
                pass

        # 3) AkShare 通用新闻兜底（按公司名关键词过滤）
        try:
            frames.append(self._fetch_akshare_general_news(name, limit=limit))
        except Exception:
            pass

        # 仅保留非空 DataFrame，避免 pd.concat([]) 抛错
        non_empty = [f for f in frames if f is not None and not f.empty]
        if not non_empty:
            return pd.DataFrame()

        df = pd.concat(non_empty, ignore_index=True)

        # 标准字段保证
        for col in ["title", "url", "summary", "source"]:
            if col not in df:
                df[col] = None
        if "published_at" in df:
            df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
        else:
            df["published_at"] = pd.NaT

        df["symbol"] = code or name
        df["company_name"] = name

        # 去重（按 title+url），最新在前
        df.sort_values(["published_at"], ascending=[False], inplace=True)
        df = df.drop_duplicates(subset=["title", "url"], keep="first")

        # 时间窗口过滤
        s = _ensure_date(since) if since else None
        u = _ensure_date(until) if until else None
        if s:
            sdt = pd.to_datetime(s)
            df = df[(df["published_at"].isna()) | (df["published_at"] >= sdt)]
        if u:
            # 包含截止日整天
            udt = pd.to_datetime(u) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            df = df[(df["published_at"].isna()) | (df["published_at"] <= udt)]

        return df.head(limit)


# =========================
# 单字典参数的便捷入口（兼容旧调用）
# =========================
_DEF_NEWS: Optional[UnifiedNewsTool] = None

def _coerce_news_params(
    params: Optional[T.Union[dict, str]] = None,
    **kwargs,
) -> dict:
    """
    统一解析参数为 dict：
    - params 为 dict：直接使用
    - params 为 str：视为 symbol_or_name
    - 兼容旧式 kwargs：symbol_or_name=..., limit=..., since=..., until=...
    字段：
      symbol_or_name: str       # 必填
      limit: int = 50
      since: "YYYY-MM-DD" | "YYYYMMDD" | None
      until: "YYYY-MM-DD" | "YYYYMMDD" | None
    """
    if params is None:
        params = {}
    if isinstance(params, str):
        params = {"symbol_or_name": params}
    if not isinstance(params, dict):
        raise ToolError("params must be a dict or a symbol/name string")

    merged = {**params, **kwargs}
    q = merged.get("symbol_or_name") or merged.get("query") or merged.get("symbol") or merged.get("name")
    if not q or not str(q).strip():
        raise ToolError("`symbol_or_name` is required in params dict")

    limit = int(merged.get("limit", 50))
    since = merged.get("since")
    until = merged.get("until")

    limit = max(1, min(limit, 200))  # 安全上限

    return {"symbol_or_name": str(q).strip(), "limit": limit, "since": since, "until": until}

def get_company_news_united(
    params: Optional[T.Union[dict, str]] = None,
    **kwargs,
) -> Dict[str, T.Any]:
    """
    单参数（dict）入口 —— 适配只能传一个参数给 Agent 的场景。

    参数字典 schema：
    {
      "symbol_or_name": "600519" | "贵州茅台",   # 必填
      "limit": 50,                               # 选填，1~200
      "since": "YYYY-MM-DD" | "YYYYMMDD",        # 选填
      "until": "YYYY-MM-DD" | "YYYYMMDD"         # 选填
    }

    兼容旧式调用：get_company_news_united("600519", limit=40, since="2025-01-01")
    """
    p = _coerce_news_params(params, **kwargs)

    global _DEF_NEWS
    if _DEF_NEWS is None:
        _DEF_NEWS = UnifiedNewsTool()

    df = _DEF_NEWS.get_company_news(
        p["symbol_or_name"],
        limit=p["limit"],
        since=p["since"],
        until=p["until"],
    )

    payload: Dict[str, T.Any] = {
        "query": p["symbol_or_name"],
        "rows": [],
        "vendor_meta": {"vendor": "eastmoney+sina+akshare", "cached": False},
    }

    if df is None or df.empty:
        return payload

    out = df.copy()
    if "published_at" in out:
        out["published_at"] = out["published_at"].dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")

    payload["rows"] = out[
        ["published_at", "title", "summary", "url", "source", "symbol", "company_name"]
    ].to_dict(orient="records")

    return payload
