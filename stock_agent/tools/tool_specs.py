def get_openai_tool_specs():
    return [
        {
            "name": "list_a_share_industry_keywords",
            "description": "列出东财/AkShare 提供的全部 A股行业关键字清单（行业名+行业代码）。",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "get_a_share_list_by_exact_industry",
            "description": "按精确行业名获取成分股（不做模糊）。行业名必须来自行业关键字清单。",
            "parameters": {
                "type": "object",
                "properties": {
                    "industry_name": {"type": "string", "description": "行业名（来自 list_a_share_industry_keywords 的 industry 字段）"},
                    "limit": {"type": "integer", "default": 30},
                    "include_names": {"type": "boolean", "default": False},
                },
                "required": ["industry_name"],
            },
        },
        # 原有两个工具也可以保留
        {
            "name": "get_stock_market_data_united",
            "description": "获取A股日线行情（支持前/后复权），统一字段输出。",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "start_date": {"type": "string", "nullable": True},
                    "end_date": {"type": "string", "nullable": True},
                    "adj": {"type": "string", "enum": ["qfq", "hfq", "none"], "default": "qfq"},
                },
                "required": ["symbol"],
            },
        },
        {
            "name": "get_company_news_united",
            "description": "获取A股公司相关新闻（Eastmoney+Sina+AkShare），统一字段输出。",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol_or_name": {"type": "string"},
                    "limit": {"type": "integer", "default": 50},
                    "since": {"type": "string", "nullable": True},
                    "until": {"type": "string", "nullable": True},
                },
                "required": ["symbol_or_name"],
            },
        },
    ]
