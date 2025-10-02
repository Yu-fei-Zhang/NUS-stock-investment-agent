from langchain_core.tools import StructuredTool


# Runnable --> BaseTool --> StructuredTool, Tool
#                       --> Custom Tool Classes

# tools定义示例
def search_function(query: str):
    return "LangChain"
search1 = StructuredTool.from_function(
    func=search_function,
    name="Search",
    description="useful for when you need to answer questions about current events"
)




