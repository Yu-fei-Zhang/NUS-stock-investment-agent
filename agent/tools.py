from abc import ABC, abstractmethod

from langchain_core.tools import StructuredTool


class ExecutionResult(ABC):
    """
    抽象类，表示工具执行的结果。
    """
    pass

class Tool(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, *args) -> ExecutionResult:
        """
        执行工具，并返回结果。
        :return: 工具执行结果字符串
        """

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




