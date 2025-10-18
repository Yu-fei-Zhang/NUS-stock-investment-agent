from alpha_vantage_client import client
from typing import List, Dict
import random

def search_stocks(keywords: str = "", limit: int = 10) -> List[Dict[str, str]]:
    """
    Search stocks by keywords and return list of {'code': ..., 'name': ...}

    Args:
        keywords: Search term (e.g., "healthcare", "technology")
        limit: Maximum initial results to fetch (max 50)
        random_count: Number of random results to return from initial list

    Returns:
        List of dictionaries with 'code' (stock symbol) and 'name' (company name)
    """
    # Validate input keywords
    keywords = keywords.strip() or "stock"  # Ensure non-empty

    # Fetch data from Alpha Vantage API
    try:
        response = client._request(
            function="SYMBOL_SEARCH",
            params={"keywords": keywords}
        )
    except Exception as e:
        raise RuntimeError(f"API request failed: {str(e)}")

    # Extract and format results
    raw_results = response.get("bestMatches", [])[:limit]  # Get up to 'limit' results
    formatted_results = []

    for item in raw_results:
        # Only include entries with both code and name
        if item.get("1. symbol") and item.get("2. name"):
            formatted_results.append({
                "code": item["1. symbol"],  # Stock symbol as 'code'
                "name": item["2. name"]  # Company name as 'name'
            })

    return formatted_results


# Test the function
if __name__ == "__main__":
    try:
        # Example 1: Search for healthcare stocks
        healthcare = search_stocks(keywords="healthcare")
        print("Healthcare stocks sample:")
        print(healthcare)  # Will show [{...}, {...}, {...}]

        # Example 2: Search for technology stocks
        tech = search_stocks(keywords="technology")
        print("\nTechnology stocks sample:")
        print(tech)  # Will show [{...}, {...}]

    except Exception as e:
        print(f"Error: {e}")