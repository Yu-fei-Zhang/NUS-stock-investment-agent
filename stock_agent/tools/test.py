from stock_agent.tools import list_a_share_industry_keywords,get_a_share_list_by_exact_industry

from stock_agent.tools import get_stock_market_data_united, get_company_news_united
# 1) 先给用户展示行业清单
catalog = list_a_share_industry_keywords()
print("行业数量:", catalog["vendor_meta"]["count"])
print(catalog["rows"][:25])  # 前10个行业关键字

# 2) 用户从清单中挑选一个行业名，例如 "半导体"
picked = get_a_share_list_by_exact_industry("贵金属", limit=30, include_names=True)
print(picked["vendor_meta"])
print(picked["rows"][:5])


# 行情（日线K）— 默认前复权
k = get_stock_market_data_united("002716", start_date="2025-10-10", adj="qfq")
# 新闻（近 40 条，自 2024-01-01 起）002716
n = get_company_news_united("002716", limit=40, since="2024-10-01")

print(k)
print(n)
