# ──────────────────────────────────────────────────────────────────────────────
# File: stock_agent/tools/unified_news.py
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

from typing import Optional, List, Dict, Any
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


# ---------------------------
# Helpers
# ---------------------------

def _today_str() -> str:
    """Return today's date as 'YYYY-MM-DD' (local)."""
    return dt.date.today().strftime("%Y-%m-%d")


def _rename_like(df: pd.DataFrame, mapping: Dict[T.Union[str, tuple], str]) -> pd.DataFrame:
    rename = {}
    for srcs, dst in mapping.items():
        src_list = (srcs,) if isinstance(srcs, str) else list(srcs)
        for c in src_list:
            if c in df.columns:
                rename[c] = dst
                break
    if rename:
        df = df.rename(columns=rename)
    return df


# ---------------------------
# Main Tool
# ---------------------------

class UnifiedNewsTool:
    """
    A股统一新闻工具（Eastmoney + Sina + AkShare 兜底）

    统一输出字段（DataFrame）:
      - published_at: pd.Timestamp（本地无 tz）
      - title: str
      - summary: str | None
      - url: str
      - source: "eastmoney" | "sina" | "akshare"
      - symbol: str（代码）
      - company_name: str
    """

    def __init__(self, rate_limit: Optional[RateLimiter] = None):
        self.rl = rate_limit or RateLimiter(rate=3, capacity=6)
        self._ak = None

    def _ensure_ak(self):
        if self._ak is None:
            self._ak = _lazy_import("akshare")
        return self._ak

    def _code_to_name(self, code: str) -> Optional[str]:
        """通过 AkShare 映射 A 股代码 -> 公司名；失败则返回 None。"""
        ak = self._ensure_ak()
        self.rl.acquire()
        try:
            df = with_retries(ak.stock_info_a_code_name)()
        except Exception:
            return None
        if df is None or df.empty:
            return None
        df = _rename_like(df, {("code", "代码"): "code", ("name", "名称"): "name"})
        row = df[df.get("code", pd.Series(dtype=str)) == code]
        if not row.empty:
            return str(row.iloc[0].get("name", None))
        return None

    # ---------------------------
    # Vendors
    # ---------------------------
    def _fetch_eastmoney_search(self, keyword: str, limit: int = 80) -> pd.DataFrame:
        """
        抓取东财搜索页（HTML），适配多入口与 DOM 变化。
        以“公司名”作为关键字。
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

        url_candidates = [
            ("https://so.eastmoney.com/news/s", "keyword"),
            ("https://so.eastmoney.com/news/s", "KeyWord"),
            ("https://so.eastmoney.com/web/s",  "keyword"),
            ("https://so.eastmoney.com/web/s",  "KeyWord"),
        ]

        items: List[Dict[str, Any]] = []
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

    def _fetch_sina_stock_news(self, sina_symbol: str, pages: int = 3) -> pd.DataFrame:
        """
        抓取新浪个股新闻分页（HTML）。注意 GBK/GB2312 编码！
        sina_symbol 示例：'sh600519' / 'sz000001'
        """
        try:
            import requests
            from bs4 import BeautifulSoup
        except Exception:
            return pd.DataFrame()

        items: List[Dict[str, Any]] = []
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
                r.encoding = "gb18030"  # 明确按 GB 解码
                return r.text

            html = with_retries(_get_text)()
            soup = BeautifulSoup(html, "lxml")

            candidates = []
            candidates += soup.select("#newslist a[target='_blank']")
            candidates += soup.select("div.datelist a[target='_blank']")
            candidates += soup.select("ul#newslist2 li a[target='_blank']")
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

    def _fetch_akshare_general_news(self, keyword: str, limit: int = 80) -> pd.DataFrame:
        """
        使用 AkShare 通用财经新闻接口，按关键词（公司名）过滤标题。
        """
        ak = self._ensure_ak()
        self.rl.acquire()
        try:
            df = with_retries(ak.stock_news_em)()
        except Exception:
            return pd.DataFrame()

        if df is None or df.empty:
            return pd.DataFrame()

        df = _rename_like(df, {
            ("标题", "title"): "title",
            ("摘要", "content", "summary"): "summary",
            ("链接", "url"): "url",
            ("时间", "发布时间", "publish_time"): "published_at",
        })
        if "title" not in df:
            return pd.DataFrame()

        m = df["title"].astype(str).str.contains(keyword, case=False, na=False)
        out = df.loc[m].copy()
        out["source"] = "akshare"
        if "published_at" in out:
            out["published_at"] = pd.to_datetime(out["published_at"], errors="coerce")

        return out.head(limit)

    # ---------------------------
    # Public: by symbol only
    # ---------------------------
    def get_company_news_by_code(
        self,
        symbol: str,
        limit: int = 80,
        since: str = "2024-10-01",
        until: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        仅接收“股票代码/带交易所前后缀的代码”。
        默认时间窗口：自 2024-10-01 至今天（含）。
        """
        # 解析为标准结构
        sym = normalize_symbol(symbol)
        code = sym["code"]
        company_name = self._code_to_name(code) or code
        sina_symbol = sym.get("sina", None)

        # 默认 today（YYYY-MM-DD）
        if not until:
            until = _today_str()

        frames: List[pd.DataFrame] = []

        # 1) Eastmoney 搜索（按公司名）
        try:
            frames.append(self._fetch_eastmoney_search(company_name, limit=limit))
        except Exception:
            pass

        # 2) Sina 个股新闻（按 sina_symbol）
        if sina_symbol:
            try:
                pages = max(1, min(3, int(math.ceil(limit / 30))))
                frames.append(self._fetch_sina_stock_news(sina_symbol, pages=pages))
            except Exception:
                pass

        # 3) AkShare 通用新闻兜底（按公司名关键词）
        try:
            frames.append(self._fetch_akshare_general_news(company_name, limit=limit))
        except Exception:
            pass

        non_empty = [f for f in frames if f is not None and not f.empty]
        if not non_empty:
            return pd.DataFrame()

        df = pd.concat(non_empty, ignore_index=True)

        # 标准字段完善
        for col in ["title", "url", "summary", "source"]:
            if col not in df:
                df[col] = None
        if "published_at" in df:
            df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
        else:
            df["published_at"] = pd.NaT

        df["symbol"] = code
        df["company_name"] = company_name

        # 去重 & 排序
        df.sort_values(["published_at"], ascending=[False], inplace=True)
        df = df.drop_duplicates(subset=["title", "url"], keep="first")

        # 时间窗口过滤（含边界）
        s = _ensure_date(since) if since else None
        u = _ensure_date(until) if until else None
        if s:
            sdt = pd.to_datetime(s)
            df = df[(df["published_at"].isna()) | (df["published_at"] >= sdt)]
        if u:
            udt = pd.to_datetime(u) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            df = df[(df["published_at"].isna()) | (df["published_at"] <= udt)]

        return df.head(limit)


# 便于直接使用的 JSON Facade（仅一个参数：股票代码）
_DEF_NEWS: Optional[UnifiedNewsTool] = None

def get_company_news_united(symbol: str) -> Dict[str, Any]:
    """
    便捷入口：只传一支 A 股代码（支持 '600519' / '600519.SH' / 'sh600519'）。
    默认新闻时间窗口：自 2024-10-01 至今天（含）。

    返回 JSON:
    {
      "symbol": "<输入的代码>",
      "rows": [
        {"published_at":"YYYY-MM-DD HH:MM:SS","title":"...","summary":"...","url":"...","source":"...","symbol":"600519","company_name":"贵州茅台"},
        ...
      ],
      "vendor_meta": {"vendor": "eastmoney+sina+akshare", "cached": False, "since": "2024-10-01", "until": "YYYY-MM-DD"}
    }
    """
    global _DEF_NEWS
    if _DEF_NEWS is None:
        _DEF_NEWS = UnifiedNewsTool()

    since = "2024-10-01"
    until = _today_str()

    df = _DEF_NEWS.get_company_news_by_code(symbol, limit=80, since=since, until=until)

    payload: Dict[str, Any] = {
        "symbol": symbol,
        "rows": [],
        "vendor_meta": {"vendor": "eastmoney+sina+akshare", "cached": False, "since": since, "until": until},
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
