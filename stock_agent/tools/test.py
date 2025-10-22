
from stock_agent.tools.unified_market_data import get_stock_market_data_united
from stock_agent.tools.unified_news import get_company_news_united
# from stock_agent.tools.industry_picker import list_a_share_industry_keywords, get_a_share_list_by_exact_industry
#
# # 1) 先给用户展示行业清单
# catalog = list_a_share_industry_keywords()
# print("行业数量:", catalog["vendor_meta"]["count"])
# print(catalog["rows"][:86])  # 前10个行业关键字
#
# # 2) 用户从清单中挑选一个行业名，例如 "半导体"
# picked = get_a_share_list_by_exact_industry (industry_name="航运港口",limit=10,include_names=True)
# print(picked["rows"][:5])

from stock_agent.tools.industry_picker import get_random_a_share_sequence
# from stock_agent.tools.tools_CN_A_share import a_share_random_industry_picks_tool
# print(a_share_random_industry_picks_tool.invoke({}))
# print(a_share_random_industry_picks_tool.run("1"))# LangChain 调用时可传空 dict
# #print(get_random_a_share_sequence())
# print(get_stock_market_data_united("600519"))
# # 如果想更严格限速（避免东财断连）：
# picker = IndustryCatalogTool(rate_limit=RateLimiter(rate=1.0, capacity=3))
# df = picker.get_random_top_sequence(k_industries=5, total_stocks=5, seed=123, include_names=True)
# print(df)
# print(get_company_news_united("600519"))
# k1=get_stock_market_data_united({"symbol":"600519","start_date":"2025-10-10","end_date":"2025-10-19"})
# print(k1)
# k = get_stock_market_data_united("600519", start_date="2025-10-10", adj="qfq")
# print(k)

# n = get_company_news_united("600519", limit=40, since="2024-10-01")
# print(n)
# n1=get_company_news_united({"symbol_or_name":"600519", "limit":40, "since":"2025-01-01"})
# print(n1)
from stock_agent.tools.unified_fundamentals import get_a_share_fundamentals
print(get_a_share_fundamentals("601998"))