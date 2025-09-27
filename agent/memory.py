from abc import ABC, abstractmethod

from langchain.chains.llm import LLMChain
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory, ChatMessageHistory
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import OpenAI, ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter


# MemoryMessage 是所有记忆消息的抽象基类。
# 其子类可用于表示存储在 MySQL、Redis、向量数据库等不同后端中的一条数据。
# 通过继承该类，可以统一管理和操作各种类型的记忆数据。
class MemoryMessage(ABC):
    pass

# MemoryManager 是记忆管理的抽象基类，定义了通用的记忆操作接口。
# 子类可实现具体的存储和检索逻辑，支持多种后端（如数据库、缓存、向量存储等）。
class MemoryManager(ABC):
    @abstractmethod
    def get_memory_by_key(self, key: str) -> MemoryMessage:
        """
        抽象方法：根据 key 获取对应的 memory。
        子类需实现具体的检索逻辑。
        :param key: memory 的唯一标识
        :return: MemoryMessage 实例，代表一条记忆数据
        """
        pass

    @abstractmethod
    def get_memories_by_keys(self, key: list) -> list[MemoryMessage]:
        """
        抽象方法：根据 keys 获取对应的 memories。
        子类需实现具体的检索逻辑。
        :param key: memory 唯一标识列表
        :return: MemoryMessage 实例列表
        """
        pass

    @abstractmethod
    def put_memory_by_key(self, key: str):
        """
        抽象方法：根据 key 存储对应的 memory。
        子类需实现具体的存储逻辑。
        :param key: memory 的唯一标识
        """
        pass

    @abstractmethod
    def put_memories_by_keys(self, key: list):
        """
        抽象方法：根据 key 存储对应的 memory。
        子类需实现具体的存储逻辑。
        :param key: memory 唯一标识列表
        """
        pass

# short-term memory
# ConversationBufferMemory
llm = OpenAI(model="gpt-4o-mini", temperature=0)
template = """你可以与人类对话。 当前对话: {history} 人类问题: {question} 回复:"""
prompt = PromptTemplate.from_template(template)
memory = ConversationBufferMemory()
chain = LLMChain(llm=llm, prompt=prompt, memory=memory)
chain.invoke({"question": "我的名字叫Tom"})

prompt = ChatPromptTemplate.from_messages([
    ("system","你是一个与人类对话的机器人。"),
    MessagesPlaceholder(variable_name='history'),
    ("human","问题：{question}")
])
memory = ConversationBufferMemory(return_messages=True)
llm_chain = LLMChain(prompt=prompt,llm=llm, memory=memory)
res1 = llm_chain.invoke({"question": "中国首都在哪里？"})

#
memory = ConversationBufferWindowMemory(k=2)
# 3.保存消息
memory.save_context({"input": "你好"}, {"output": "怎么了"})
memory.save_context({"input": "你是谁"}, {"output": "我是AI助手"})
memory.save_context({"input": "你的生日是哪天？"}, {"output": "我不清楚"})

# RAG
prompt_template = """请使用以下提供的文本内容来回答问题。仅使用提供的文本信息，如果文本中
没有相关信息，请回答"抱歉，提供的文本中没有这个信息"。
文本内容：
{context}
问题：{question}
回答：
"
"""
prompt = PromptTemplate.from_template(prompt_template)
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)
embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")
loader = TextLoader("./asset/load/10-test_doc.txt", encoding='utf-8')
documents = loader.load()
# 5. 分割文档
text_splitter = CharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
)
texts = text_splitter.split_documents(documents)
vectorstore = FAISS.from_documents(
    documents=texts,
    embedding=embedding_model
)
retriever = vectorstore.as_retriever()
docs = retriever.invoke("北京有什么著名的建筑？")
chain = prompt | llm
result = chain.invoke(input={"question":"北京有什么著名的建筑？","context":docs})
print("\n回答:", result.content)