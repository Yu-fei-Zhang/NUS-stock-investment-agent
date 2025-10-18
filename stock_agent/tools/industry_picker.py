# ──────────────────────────────────────────────────────────────────────────────
# File: stock_agent/tools/industry_picker.py
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import typing as T
import pandas as pd

from stock_agent.tools.common import (
    ToolError,
    RateLimiter,
    _lazy_import,
    with_retries,
)


def _rename_like(df: pd.DataFrame, mapping: T.Dict[T.Union[str, tuple], str]) -> pd.DataFrame:
    """把多种可能的列名统一重命名为标准列名"""
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


def _ensure_code(df: pd.DataFrame) -> pd.DataFrame:
    if "code" not in df.columns:
        raise ToolError("结果缺少代码列，请检查 akshare 接口变更")
    df["code"] = df["code"].astype(str).str.zfill(6)
    return df


class IndustryCatalogTool:
    """
    行业目录工具：
    1) 列出东财（AkShare）里**全部行业关键字**（行业名 + 行业代码）
    2) 用户从清单里选中“行业名”后，精确获取该行业的成分股（不做模糊）
    """

    def __init__(self, rate_limit: RateLimiter | None = None):
        self.rl = rate_limit or RateLimiter(rate=3.0, capacity=6)
        self._ak = None

    # ---------- lazy deps ----------
    def _ensure_ak(self):
        if self._ak is None:
            self._ak = _lazy_import("akshare")
        return self._ak

    # ---------- public APIs ----------
    def list_industry_keywords(self) -> pd.DataFrame:
        """
        返回东财行业清单（DataFrame）：
        columns: industry, code
        """
        ak = self._ensure_ak()
        self.rl.acquire()
        try:
            df = with_retries(ak.stock_board_industry_name_em)()
        except Exception as e:
            raise ToolError(f"获取东财行业清单失败: {e}")

        if df is None or df.empty:
            raise ToolError("东财行业清单为空")

        df = _rename_like(
            df,
            {("板块名称", "行业名称", "名称", "name", "板块"): "industry",
             ("代码", "板块代码", "code"): "code"}
        )
        if "industry" not in df.columns:
            raise ToolError("无法识别行业名称列，请检查 akshare 接口变更")
        df["industry"] = df["industry"].astype(str)
        # 仅保留两列，稳定输出
        out = df[["industry", "code"]].copy()
        # 附带元信息
        out.attrs["vendor_meta"] = {"vendor": "eastmoney", "count": len(out)}
        return out

    def get_constituents_by_exact_industry(
        self,
        industry_name: str,
        limit: int = 30,
        include_names: bool = False,
        sort_by: str | None = "total_mv",
        ascending: bool = False,
    ) -> pd.DataFrame:
        """
        精确按“行业名”获取成分股（不做模糊匹配）。
        - industry_name 必须来自 list_industry_keywords() 的 industry 字段
        - 返回列：["code"] 或 ["code","name"]（include_names=True）
        """
        # 先验证行业名确实存在于清单（避免拼写问题）
        catalog = self.list_industry_keywords()
        names = set(catalog["industry"].tolist())
        if industry_name not in names:
            # 给出提示：展示可选行业数量，不做模糊
            raise ToolError(
                f"未找到行业：{industry_name}。请先从 list_industry_keywords() 的清单中拷贝合法行业名。"
            )

        ak = self._ensure_ak()
        self.rl.acquire()
        try:
            df = with_retries(ak.stock_board_industry_cons_em)(symbol=industry_name)
        except Exception as e:
            raise ToolError(f"获取行业[{industry_name}]成分股失败: {e}")

        if df is None or df.empty:
            raise ToolError(f"行业[{industry_name}]暂无成分股")

        df = _rename_like(
            df,
            {
                ("代码", "code"): "code",
                ("名称", "name"): "name",
                ("总市值", "总市值-亿", "总市值(元)", "总市值（元）", "market_cap", "总市值(万元)"): "total_mv",
            },
        )
        df = _ensure_code(df)

        if sort_by and sort_by in df.columns:
            df = df.sort_values(sort_by, ascending=ascending, kind="mergesort")

        keep_cols = ["code", "name"] if (include_names and "name" in df.columns) else ["code"]
        out = df[keep_cols].head(int(limit)).reset_index(drop=True).copy()
        out.attrs["vendor_meta"] = {
            "vendor": "eastmoney_industry",
            "industry": industry_name,
            "limit": int(limit),
            "sort_by": sort_by,
            "ascending": ascending,
        }
        return out


# 便于 LLM/HTTP 直接使用的 JSON 封装
_DEF_CATALOG: IndustryCatalogTool | None = None


def list_a_share_industry_keywords() -> T.Dict[str, T.Any]:
    """
    返回 JSON：
    {
      "source": "eastmoney",
      "rows": [{"industry": "...", "code": "BKxxxx"}, ...],
      "vendor_meta": {"vendor": "eastmoney", "count": N}
    }
    """
    global _DEF_CATALOG
    if _DEF_CATALOG is None:
        _DEF_CATALOG = IndustryCatalogTool()

    df = _DEF_CATALOG.list_industry_keywords()
    meta = df.attrs.get("vendor_meta", {})
    return {
        "source": "eastmoney",
        "rows": df.to_dict(orient="records"),
        "vendor_meta": meta,
    }


def get_a_share_list_by_exact_industry(
    industry_name: str,
    limit: int = 30,
    include_names: bool = False,
) -> T.Dict[str, T.Any]:
    """
    精确行业名 → 成分股 JSON：
    {
      "industry": "<行业名>",
      "codes": ["600519", "000001", ...],
      "rows": [{"code":"600519","name":"贵州茅台"}, ...],  # include_names=True 时包含
      "vendor_meta": {...}
    }
    """
    global _DEF_CATALOG
    if _DEF_CATALOG is None:
        _DEF_CATALOG = IndustryCatalogTool()

    df = _DEF_CATALOG.get_constituents_by_exact_industry(
        industry_name=industry_name,
        limit=limit,
        include_names=include_names,
    )
    meta = df.attrs.get("vendor_meta", {})
    payload: T.Dict[str, T.Any] = {
        "industry": meta.get("industry", industry_name),
        "codes": df["code"].tolist(),
        "vendor_meta": meta,
    }
    if include_names and "name" in df.columns:
        payload["rows"] = df.to_dict(orient="records")
    return payload
