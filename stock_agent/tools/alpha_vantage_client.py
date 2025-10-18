import requests
import json
import os

class AlphaVantageClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.default_timeout = 10

    def _request(self, function, params=None):
        """Encapsulates all details of API communication and provides a simple interface externally.
        You only need to pass in the function (API feature) and additional parameters to retrieve data and handle common errors."""
        params = params or {}
        params.update({
            "function": function,
            "apikey": self.api_key,
            "datatype": "json"
        })

        try:
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.default_timeout
            )
            response.raise_for_status()
            data = response.json()

            # 处理API错误信息
            if "Error Message" in data:
                raise ValueError(f"API Error: {data['Error Message']}")
            if "Information" in data:
                raise Warning(f"API Info: {data['Information']}")

            return data

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Request failed: {str(e)}")

#Load the api from the env.txt
def load_api_key_from_env_file(file_path=r"E:\Translator2\NUS-stock-investment-agent\env.txt"):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"环境文件 {file_path} 不存在")

    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("ALPHA_VANTAGE_API_KEY="):
                # 提取等号后的密钥部分
                return line.split("=", 1)[1]  # 用split("=", 1)避免密钥中含等号的情况
    raise ValueError(f"在 {file_path} 中未找到 ALPHA_VANTAGE_API_KEY")


# Initialization
api_key = load_api_key_from_env_file()
client = AlphaVantageClient(api_key=api_key)

#Testing the client as a using example
if __name__ == "__main__":
    try:
        # Call Alpha Vantage's "GLOBAL_QUOTE" endpoint (retrieves latest stock quote, simple for verification)
        # Example: Apple Inc. (ticker: AAPL)
        response = client._request(
            function="GLOBAL_QUOTE",
            params={"symbol": "TSLA"}
        )

        # Print results (simplified to key information)
        print("===== Test Results =====")
        if "Global Quote" in response:
            quote = response["Global Quote"]
            print(f"Ticker: {quote.get('01. symbol', 'Unknown')}")
            print(f"Latest Price: {quote.get('05. price', 'Unknown')}")
            print(f"Open Price: {quote.get('02. open', 'Unknown')}")
            print(f"Day's High: {quote.get('03. high', 'Unknown')}")
            print(f"Day's Low: {quote.get('04. low', 'Unknown')}")
        else:
            print("No stock quote data retrieved. Raw response:", response)

    except Exception as e:
        print(f"Test failed. Error message: {str(e)}")