import os
from typing import Optional, Type, Union, List
from pydantic import BaseModel, Field, ConfigDict
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from stock_agent.memory.Long_termMemory import Init_Models, Build_Vectorstore, RAG_QA


class RAGQAArgs(BaseModel):
    """
    RAG 问答工具的输入参数模型。

    Attributes:
        question (str): 用户输入的问题，例如“北京有哪些著名建筑？”
    """
    question: str = Field(
        ...,
        description="需要根据文档内容回答的问题，例如：'北京有哪些著名建筑？'"
    )


class RAGQATool(BaseTool):
    """
    封装 RAG（Retrieval-Augmented Generation）问答流程的 LangChain 工具类。

    功能：
        - 从向量数据库（FAISS）检索相关文档；
        - 调用 LLM（ChatOpenAI）生成基于文档的回答；
        - 支持多文件或文件夹批量加载。
    """

    name: str = "rag_qa_tool"
    description: str = (
        "基于 FAISS 向量数据库与 ChatOpenAI 模型的文档问答工具，"
        "能够从本地文本中检索信息并生成上下文相关的回答。"
    )
    args_schema: Type[BaseModel] = RAGQAArgs

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        vectorstore: Optional[FAISS] = None,
        file_path: Union[str, List[str]] = "../../Resource/docs",
        index_path: str = "faiss_index",
        rebuild_index: bool = False,
        **kwargs,
    ):
        """
        初始化 RAGQATool 实例。

        Args:
            llm (Optional[ChatOpenAI]): 语言模型实例，若未提供则自动初始化。
            vectorstore (Optional[FAISS]): 向量数据库实例，若未提供则自动构建。
            file_path (Union[str, List[str]]): 支持单文件、多文件或文件夹路径。
            index_path (str): FAISS 索引保存路径。
            rebuild_index (bool): 是否强制重新构建索引。
            **kwargs: 传递给父类 BaseTool 的参数。
        """
        super().__init__(**kwargs)

        # 初始化 LLM
        self._llm = llm or Init_Models()[0]

        # 若指定强制重建索引，则删除旧索引
        if rebuild_index and os.path.exists(index_path):
            import shutil
            print(f"检测到 rebuild_index=True，正在删除旧索引：{index_path}")
            shutil.rmtree(index_path, ignore_errors=True)

        # 构建或加载向量数据库
        self._vectorstore = vectorstore or Build_Vectorstore(
            file_path=file_path,
            index_path=index_path
        )

    @property
    def llm(self) -> ChatOpenAI:
        """返回当前使用的语言模型实例。"""
        return self._llm

    @property
    def vectorstore(self) -> FAISS:
        """返回当前使用的向量数据库实例。"""
        return self._vectorstore

    def _run(self, **kwargs) -> str:
        """
        同步执行 RAG 问答流程。
        """
        try:
            question = kwargs.get("question", "")
            if not question:
                return "未提供 question 参数。"

            return RAG_QA(question, self.vectorstore, self.llm, k=15)
        except Exception as e:
            return f"执行 RAG 问答时发生错误: {str(e)}"

    async def _arun(self, **kwargs) -> str:
        """
        异步执行 RAG 问答流程。
        """
        return self._run(**kwargs)


if __name__ == "__main__":

    tool = RAGQATool()

    # 测试问题
    questions = [
        "北京有什么著名的建筑？",
        "北京和上海分别有什么大学？",
        "上海是中国的首都吗？",
    ]

    for q in questions:
        print(f"\n问题：{q}")
        answer = tool.run({"question": q})
        print(f"回答：{answer}")
