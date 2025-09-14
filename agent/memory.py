from langchain.memory import ConversationBufferMemory, VectorStoreRetrieverMemory
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings

# 短期记忆：会话缓冲区
def get_stm():
    return ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# 长期记忆：向量数据库（FAISS）
def get_ltm():
    embedding = OpenAIEmbeddings()
    vectorstore = FAISS(embedding_function=embedding)
    return VectorStoreRetrieverMemory(vectorstore=vectorstore)

class MemoryManager:
    def __init__(self):
        self.stm = get_stm()
        self.ltm = get_ltm()

    def save_stm(self, key, value):
        # 可扩展为存储到 ConversationBufferMemory
        setattr(self.stm, key, value)

    def get_stm(self, key):
        return getattr(self.stm, key, None)

    def save_ltm(self, stock, report):
        # 可扩展为存储到 FAISS/SQL
        pass

    def get_ltm(self, stock):
        # 可扩展为从 FAISS/SQL 检索
        pass
