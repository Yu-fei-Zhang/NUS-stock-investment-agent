from abc import ABC, abstractmethod

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



