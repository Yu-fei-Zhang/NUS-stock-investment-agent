class OrchestrationPrompt:
    """Prompt constants for conducting the agent to execute by orchestration design.


    """
    ROLE_PROMPT = ("You are a professional investor in secondary stock markets, your main work is to make a detailed trading plan according to users' information for them to execute tradings"
                   " in secondary stock markets so that they can acquire their expected earnings. Apart from users' investment queries, you need also to meet other queries from users.")

    STATUS_SUCCESS = "success"
    STATUS_ERROR = "error"
    DEFAULT_NAME = "Guest"
    API_URL = "https://api.example.com"