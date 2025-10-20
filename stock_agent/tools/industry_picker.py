# ──────────────────────────────────────────────────────────────────────────────
# File: stock_agent/tools/industry_picker.py
# Random K industries (from a fixed Eastmoney list) -> pick top N per industry
# Source: Eastmoney via AkShare
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import random
import typing as T
import pandas as pd

from stock_agent.tools.common import (
    ToolError,
    RateLimiter,
    _lazy_import,
    with_retries,
)

# ----------------------------
# 固定的东财行业清单（86 个）
# ----------------------------
EASTMONEY_FIXED_INDUSTRIES: list[dict] = [
    {'industry': '贵金属', 'code': 'BK0732'}, {'industry': '燃气', 'code': 'BK1028'},
    {'industry': '航空机场', 'code': 'BK0420'}, {'industry': '航运港口', 'code': 'BK0450'},
    {'industry': '银行', 'code': 'BK0475'}, {'industry': '铁路公路', 'code': 'BK0421'},
    {'industry': '煤炭行业', 'code': 'BK0437'}, {'industry': '石油行业', 'code': 'BK0464'},
    {'industry': '钢铁行业', 'code': 'BK0479'}, {'industry': '珠宝首饰', 'code': 'BK0734'},
    {'industry': '采掘行业', 'code': 'BK1017'}, {'industry': '公用事业', 'code': 'BK0427'},
    {'industry': '工程咨询服务', 'code': 'BK0726'}, {'industry': '纺织服装', 'code': 'BK0436'},
    {'industry': '农牧饲渔', 'code': 'BK0433'}, {'industry': '医药商业', 'code': 'BK1042'},
    {'industry': '中药', 'code': 'BK1040'}, {'industry': '农药兽药', 'code': 'BK0730'},
    {'industry': '商业百货', 'code': 'BK0482'}, {'industry': '化肥行业', 'code': 'BK0731'},
    {'industry': '家用轻工', 'code': 'BK0440'}, {'industry': '水泥建材', 'code': 'BK0424'},
    {'industry': '房地产开发', 'code': 'BK0451'}, {'industry': '装修装饰', 'code': 'BK0725'},
    {'industry': '食品饮料', 'code': 'BK0438'}, {'industry': '旅游酒店', 'code': 'BK0485'},
    {'industry': '物流行业', 'code': 'BK0422'}, {'industry': '化学制药', 'code': 'BK0465'},
    {'industry': '文化传媒', 'code': 'BK0486'}, {'industry': '电力行业', 'code': 'BK0428'},
    {'industry': '工程建设', 'code': 'BK0425'}, {'industry': '生物制品', 'code': 'BK1044'},
    {'industry': '多元金融', 'code': 'BK0738'}, {'industry': '综合行业', 'code': 'BK0539'},
    {'行业': '环保行业', 'code': 'BK0728'}, {'industry': '化学原料', 'code': 'BK1019'},
    {'industry': '酿酒行业', 'code': 'BK0477'}, {'industry': '美容护理', 'code': 'BK1035'},
    {'industry': '装修建材', 'code': 'BK0476'}, {'industry': '贸易行业', 'code': 'BK0484'},
    {'industry': '汽车服务', 'code': 'BK1016'}, {'industry': '塑料制品', 'code': 'BK0454'},
    {'industry': '家电行业', 'code': 'BK0456'}, {'industry': '造纸印刷', 'code': 'BK0470'},
    {'industry': '化学制品', 'code': 'BK0538'}, {'industry': '医疗器械', 'code': 'BK1041'},
    {'industry': '通信服务', 'code': 'BK0736'}, {'industry': '橡胶制品', 'code': 'BK1018'},
    {'industry': '专业服务', 'code': 'BK1043'}, {'industry': '房地产服务', 'code': 'BK1045'},
    {'industry': '证券', 'code': 'BK0473'}, {'industry': '医疗服务', 'code': 'BK0727'},
    {'industry': '保险', 'code': 'BK0474'}, {'industry': '包装材料', 'code': 'BK0733'},
    {'industry': '仪器仪表', 'code': 'BK0458'}, {'industry': '交运设备', 'code': 'BK0429'},
    {'industry': '有色金属', 'code': 'BK0478'}, {'industry': '光学光电子', 'code': 'BK1038'},
    {'industry': '工程机械', 'code': 'BK0739'}, {'industry': '计算机设备', 'code': 'BK0735'},
    {'industry': '玻璃玻纤', 'code': 'BK0546'}, {'industry': '教育', 'code': 'BK0740'},
    {'industry': '化纤行业', 'code': 'BK0471'}, {'industry': '游戏', 'code': 'BK1046'},
    {'industry': '互联网服务', 'code': 'BK0447'}, {'industry': '软件开发', 'code': 'BK0737'},
    {'industry': '专用设备', 'code': 'BK0910'}, {'industry': '能源金属', 'code': 'BK1015'},  # 修正键名
    {'industry': '船舶制造', 'code': 'BK0729'}, {'industry': '航天航空', 'code': 'BK0480'},
    {'industry': '通用设备', 'code': 'BK0545'}, {'industry': '通信设备', 'code': 'BK0448'},
    {'industry': '汽车零部件', 'code': 'BK0481'}, {'industry': '小金属', 'code': 'BK1027'},
    {'industry': '汽车整车', 'code': 'BK1029'}, {'industry': '非金属材料', 'code': 'BK1020'},
    {'industry': '电机', 'code': 'BK1030'}, {'industry': '电子化学品', 'code': 'BK1039'},
    {'industry': '电池', 'code': 'BK1033'}, {'industry': '消费电子', 'code': 'BK1037'},
    {'industry': '电子元件', 'code': 'BK0459'}, {'industry': '风电设备', 'code': 'BK1032'},
    {'industry': '半导体', 'code': 'BK1036'}, {'industry': '光伏设备', 'code': 'BK1031'},
    {'industry': '电网设备', 'code': 'BK0457'}, {'industry': '电源设备', 'code': 'BK1034'},
]
# 修正上面“能源金属”那一项的键名误填
for d in EASTMONEY_FIXED_INDUSTRIES:
    if "industry" not in d and "行业" in d:
        d["industry"] = d.pop("行业")

# ----------------------------
# 小工具
# ----------------------------
def _rename_like(df: pd.DataFrame, mapping: T.Dict[T.Union[str, tuple], str]) -> pd.DataFrame:
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
    df["code"] = df["code"].astype(str).str.extract(r"(\d{6})", expand=False).fillna("")
    df = df[df["code"].str.len() == 6].copy()
    return df

def _to_pct(x) -> float | None:
    try:
        s = str(x).replace("%", "")
        return float(s)
    except Exception:
        return None

# ----------------------------
# 主工具
# ----------------------------
class IndustryRandomTopPicker:
    """
    逻辑：
      1) 从固定 86 个东财行业中随机抽取 k 个（默认 5）
      2) 每个行业用 akshare 的 stock_board_industry_cons_em(symbol=行业名) 拉成分
      3) 以当日涨跌幅 pct_chg 作为“近期表现”度量，**每行业选择前 n_per_industry 支**
      4) 合并输出，默认总数 = k * n_per_industry（默认 5*5=25）
    """

    def __init__(self, rate_limit: RateLimiter | None = None):
        # 推荐：1.0 rps，桶 3，降低被限频概率
        self.rl = rate_limit or RateLimiter(rate=0.5, capacity=2)
        self._ak = None

    def _ensure_ak(self):
        if self._ak is None:
            self._ak = _lazy_import("akshare")
        return self._ak

    # --- 抽行业 ---
    def random_pick_industries(self, k: int = 5, seed: int | None = None) -> pd.DataFrame:
        k = max(1, min(int(k), len(EASTMONEY_FIXED_INDUSTRIES)))
        if seed is None:
            # 使用系统熵，避免每次都一样
            rnd = random.SystemRandom()
            picked = rnd.sample(EASTMONEY_FIXED_INDUSTRIES, k)
            used_seed = None
        else:
            rnd = random.Random(seed)
            pool = EASTMONEY_FIXED_INDUSTRIES.copy()
            rnd.shuffle(pool)
            picked = pool[:k]
            used_seed = seed
        df = pd.DataFrame(picked)[["industry", "code"]].copy()
        df.attrs["vendor_meta"] = {"vendor": "eastmoney", "picked": k, "seed": used_seed}
        return df

    # --- 行业成分（东财）---
    def _fetch_industry_cons(self, industry_name: str) -> pd.DataFrame:
        ak = self._ensure_ak()
        self.rl.acquire()
        df = with_retries(ak.stock_board_industry_cons_em, tries=6, delay=0.6, backoff=1.8)(
            symbol=industry_name
        )
        if df is None or df.empty:
            raise ToolError(f"行业[{industry_name}]暂无成分股或接口返回为空")
        df = _rename_like(df, {
            ("代码", "code"): "code",
            ("名称", "name"): "name",
            ("涨跌幅", "涨跌幅(%)", "pct_chg", "change_percent"): "pct_chg",
            ("总市值", "总市值-亿", "总市值(元)", "总市值（元）", "market_cap", "总市值(万元)"): "total_mv",
        })
        df = _ensure_code(df)
        if "pct_chg" in df.columns:
            df["pct_chg"] = df["pct_chg"].map(_to_pct)
        return df

    # --- 每行业取前 n 支 ---
    def _pick_top_n_from_industry(
        self,
        industry_name: str,
        n: int = 5,
        exclude_st: bool = True
    ) -> pd.DataFrame | None:
        try:
            cons = self._fetch_industry_cons(industry_name)
        except Exception:
            return None
        if exclude_st and "name" in cons.columns:
            cons = cons[~cons["name"].astype(str).str.contains(r"ST|退", regex=True, na=False)]
        # 排序：优先 pct_chg，其次 total_mv，最后任意
        if "pct_chg" in cons.columns and cons["pct_chg"].notna().any():
            cons = cons.sort_values("pct_chg", ascending=False, kind="mergesort")
        elif "total_mv" in cons.columns and cons["total_mv"].notna().any():
            cons = cons.sort_values("total_mv", ascending=False, kind="mergesort")
        # 取前 n
        take = max(1, int(n))
        topn = cons.head(take).copy()
        topn["industry"] = industry_name
        topn["rank_in_industry"] = range(1, len(topn) + 1)
        keep = ["code", "name", "industry", "rank_in_industry"]
        topn = topn[[c for c in keep if c in topn.columns]]
        return topn.reset_index(drop=True)

    # --- 对外主功能：随机 K 行业，每行业取 N 支 ---
    def get_random_top_sequence(
        self,
        k_industries: int = 5,
        n_per_industry: int = 5,
        seed: int | None = None,
        include_names: bool = True,
        exclude_st: bool = True,
        hard_cap_total: int = 30,   # 安全上限，避免一次请求太多
    ) -> pd.DataFrame:
        """
        返回 DataFrame：至少包含 ["code","industry"]，
        若 include_names=True 则包含 "name"，还包含 "rank_in_industry"。
        """
        k_industries = max(1, min(int(k_industries), len(EASTMONEY_FIXED_INDUSTRIES)))
        n_per_industry = max(1, int(n_per_industry))

        # 目标总量
        target_total = k_industries * n_per_industry
        if hard_cap_total is not None and target_total > int(hard_cap_total):
            # 若超过上限，优先缩减行业数，其次缩减每行业数量
            k_industries = min(k_industries, int(hard_cap_total // n_per_industry) or 1)
            target_total = k_industries * n_per_industry

        # 先挑行业
        picked = self.random_pick_industries(k=k_industries, seed=seed)
        tried_names = set()
        results: list[pd.DataFrame] = []

        # 先跑首批行业
        for ind in picked["industry"].tolist():
            tried_names.add(ind)
            rows = self._pick_top_n_from_industry(industry_name=ind, n=n_per_industry, exclude_st=exclude_st)
            if rows is not None and not rows.empty:
                results.append(rows)

        # 如个别行业失败，尝试从剩余行业补齐至 target_total
        if sum(len(x) for x in results) < target_total:
            remaining = [d["industry"] for d in EASTMONEY_FIXED_INDUSTRIES if d["industry"] not in tried_names]
            rnd = random.SystemRandom() if seed is None else random.Random(seed + 1)
            rnd.shuffle(remaining)
            for ind in remaining:
                rows = self._pick_top_n_from_industry(industry_name=ind, n=n_per_industry, exclude_st=exclude_st)
                if rows is not None and not rows.empty:
                    results.append(rows)
                if sum(len(x) for x in results) >= target_total:
                    break

        if not results:
            raise ToolError("未能从任何行业获取到成分股，请稍后重试或降低请求频率。")

        out = pd.concat(results, ignore_index=True)
        # 截断到总量上限
        out = out.head(target_total).reset_index(drop=True)
        if not include_names and "name" in out.columns:
            out = out.drop(columns=["name"])

        out.attrs["vendor_meta"] = {
            "vendor": "eastmoney",
            "mode": "random_industries_topN",
            "k_industries": k_industries,
            "n_per_industry": n_per_industry,
            "seed": seed,
            "exclude_st": exclude_st,
            "target_total": target_total,
            "achieved": len(out),
        }
        return out


# 兼容导出（如果你项目其他地方从 tools 导入过 IndustryCatalogTool）
IndustryCatalogTool = IndustryRandomTopPicker

# ----------------------------
# JSON 便捷封装（给 LLM / HTTP 使用）
# 单字典参数入口（兼容旧参数形式）
# ----------------------------
_DEF_PICKER: IndustryRandomTopPicker | None = None

def _coerce_picker_params(
    params: T.Optional[T.Dict[str, T.Any]] = None,
    **kwargs,
) -> T.Dict[str, T.Any]:
    """
    统一把输入解析为 dict：
    - params 为 dict：直接使用
    - 兼容旧式 kwargs：limit_industries=..., per_industry=..., seed=..., include_names=..., exclude_st=..., hard_cap_total=...
    字段：
      limit_industries: int = 5
      per_industry:     int = 5
      seed:             int | None
      include_names:    bool = True
      exclude_st:       bool = True
      hard_cap_total:   int = 30
    """
    params = params or {}
    if not isinstance(params, dict):
        raise ToolError("params must be a dict")

    merged = {**params, **kwargs}
    k = int(merged.get("limit_industries", 5))
    n = int(merged.get("per_industry", 5))
    seed = merged.get("seed", None)
    include_names = bool(merged.get("include_names", True))
    exclude_st = bool(merged.get("exclude_st", True))
    hard_cap_total = merged.get("hard_cap_total", 30)
    hard_cap_total = int(hard_cap_total) if hard_cap_total is not None else None

    # 安全上限
    if hard_cap_total is not None:
        hard_cap_total = max(1, min(hard_cap_total, 200))

    return {
        "limit_industries": max(1, min(k, len(EASTMONEY_FIXED_INDUSTRIES))),
        "per_industry": max(1, n),
        "seed": seed,
        "include_names": include_names,
        "exclude_st": exclude_st,
        "hard_cap_total": hard_cap_total,
    }

# ──────────────────────────────────────────────────────────────────────────────
# File: stock_agent/tools/industry_picker.py
# （保留上文所有类与函数；仅替换“JSON 便捷封装（给 LLM / HTTP 使用）”这一段）
# ──────────────────────────────────────────────────────────────────────────────

# ----------------------------
# JSON 便捷封装（给 LLM / HTTP 使用）
# 零参数入口：固定逻辑为随机 5 个行业 × 每行业 5 只
# ----------------------------
_DEF_PICKER: IndustryRandomTopPicker | None = None

# ----------------------------
# JSON 便捷封装（给 LLM / HTTP 使用）
# 零参数入口：固定逻辑为随机 5 个行业 × 每行业 5 只
# ----------------------------
_DEF_PICKER: IndustryRandomTopPicker | None = None

# 当实时抓取失败（Agent 环境网络受限/限频）时的离线兜底样本（只保留你需要的英文键）
FALLBACK_ROWS = [
    {"code": "600519", "name": "贵州茅台", "industry": "酿酒行业"},
    {"code": "000858", "name": "五粮液", "industry": "酿酒行业"},
    {"code": "600036", "name": "招商银行", "industry": "银行"},
    {"code": "600000", "name": "浦发银行", "industry": "银行"},
    {"code": "600276", "name": "恒瑞医药", "industry": "化学制药"},
    {"code": "600309", "name": "万华化学", "industry": "化学制品"},
    {"code": "601012", "name": "隆基绿能", "industry": "光伏设备"},
    {"code": "300750", "name": "宁德时代", "industry": "电池"},
    {"code": "002594", "name": "比亚迪", "industry": "汽车整车"},
    {"code": "000651", "name": "格力电器", "industry": "家电行业"},
    {"code": "000333", "name": "美的集团", "industry": "家电行业"},
    {"code": "600703", "name": "三安光电", "industry": "光学光电子"},
    {"code": "600104", "name": "上汽集团", "industry": "汽车整车"},
    {"code": "600030", "name": "中信证券", "industry": "证券"},
    {"code": "601318", "name": "中国平安", "industry": "保险"},
    {"code": "601888", "name": "中国中免", "industry": "旅游酒店"},
    {"code": "600028", "name": "中国石化", "industry": "石油行业"},
    {"code": "601857", "name": "中国石油", "industry": "石油行业"},
    {"code": "601088", "name": "中国神华", "industry": "煤炭行业"},
    {"code": "601225", "name": "陕西煤业", "industry": "煤炭行业"},
    {"code": "600031", "name": "三一重工", "industry": "工程机械"},
    {"code": "600900", "name": "长江电力", "industry": "电力行业"},
    {"code": "603288", "name": "海天味业", "industry": "食品饮料"},
    {"code": "002475", "name": "立讯精密", "industry": "消费电子"},
    {"code": "600585", "name": "海螺水泥", "industry": "水泥建材"},
]

def get_random_a_share_sequence() -> T.Dict[str, T.Any]:
    """
    Zero-arg entry:
      - Randomly pick 5 industries (from a fixed Eastmoney list)
      - For each industry, pick top 5 stocks by same-day % change (fallback to market cap when needed)
      - Exclude ST / “退”
      - Return ~25 stocks

    Return JSON:
      {
        "rows": [{"code":"XXXXXX","name":"Company","industry":"Industry"}, ...],
        "vendor_meta": {...}
      }
    """
    global _DEF_PICKER
    if _DEF_PICKER is None:
        _DEF_PICKER = IndustryRandomTopPicker()

    picker = _DEF_PICKER
    k, n = 5, 5
    target = k * n

    try:
        # 常规在线路径（seed=None => 每次不同）
        df = picker.get_random_top_sequence(
            k_industries=k,
            n_per_industry=n,
            seed=None,
            include_names=True,
            exclude_st=True,
            hard_cap_total=target,
        )
        meta = df.attrs.get("vendor_meta", {})
        rows_simple = []
        for _, r in df.iterrows():
            rows_simple.append({
                "code": str(r.get("code", "")),
                "name": ("" if pd.isna(r.get("name", "")) else str(r.get("name", ""))),
                "industry": ("" if pd.isna(r.get("industry", "")) else str(r.get("industry", ""))),
            })
        return {"rows": rows_simple, "vendor_meta": meta}

    except Exception as e:
        # —— 离线兜底：Agent 环境网络不通/被限频时使用 —— #
        return {
            "rows": FALLBACK_ROWS[:target],
            "vendor_meta": {
                "vendor": "fallback",
                "reason": str(e)[:200],
                "note": "Online fetch failed in agent runtime; returned static sample.",
                "target_total": target,
                "achieved": min(len(FALLBACK_ROWS), target),
            },
        }


