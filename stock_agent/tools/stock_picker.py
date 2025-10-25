from stock_agent.tools.alpha_vantage_client import client
from typing import List, Dict

def search_stocks() -> List[Dict[str, str]]:
    """
    Search stocks from five representative industries, returning 50 stocks in total (10 per industry).

    Returns:
        List of {'code': stock symbol, 'name': company name}
    """
    # 选择五个代表性行业的关键词
    industries = [
        "technology",  # 科技行业
        "healthcare",  # 医疗健康行业
        "financial",  # 金融行业
        "energy",  # 能源行业
        "consumer"  # 消费行业
    ]
    limit_per_industry = 10  # 每个行业返回10支股票
    all_stocks = []

    for keyword in industries:
        try:
            # 调用Alpha Vantage API搜索该行业股票
            response = client._request(
                function="SYMBOL_SEARCH",
                params={"keywords": keyword}
            )
        except Exception as e:
            raise RuntimeError(f"API request failed for {keyword}: {str(e)}")

        # 提取并格式化该行业的股票结果
        raw_results = response.get("bestMatches", [])[:limit_per_industry]
        for item in raw_results:
            if item.get("1. symbol") and item.get("2. name"):
                all_stocks.append({
                    "code": item["1. symbol"],
                    "name": item["2. name"]
                })

    return all_stocks


# 测试工具函数（无参数调用）
if __name__ == "__main__":
    try:
        stocks = search_stocks()
        print(f"Total stocks found: {len(stocks)}")
        print("\nSample stocks (first 5 from each industry):")

        # 按行业分组展示前5支（方便验证）
        industry_groups = [stocks[i * 10:(i + 1) * 10] for i in range(5)]
        industries = ["Technology", "Healthcare", "Financial", "Energy", "Consumer"]

        for i, group in enumerate(industry_groups):
            print(f"\n{industries[i]}:")
            for stock in group[:5]:  # 每个行业显示前5支
                print(f"{stock['code']}: {stock['name']}")

    except Exception as e:
        print(f"Error: {e}")
