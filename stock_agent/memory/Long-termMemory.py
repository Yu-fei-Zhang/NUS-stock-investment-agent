from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
import os

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_BASE_URL"] = ""

def Init_Models() -> tuple[ChatOpenAI, OpenAIEmbeddings]:
    """
    初始化大模型与嵌入模型
    """
    llm = ChatOpenAI(model="gpt-5", temperature=1)
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")
    return llm, embedding_model

def Build_Vectorstore(
    file_path: str = "../../Resource/test.txt",
    index_path: str = "faiss_index"
) -> FAISS:
    """
    构建或加载 FAISS 向量数据库
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文档文件不存在: {file_path}")

    llm, embedding_model = Init_Models()

    if os.path.exists(index_path):
        print("已加载本地向量索引")
        vectorstore = FAISS.load_local(index_path, embedding_model, allow_dangerous_deserialization=True)
        return vectorstore

    print("正在创建向量索引...")
    loader = TextLoader(file_path, encoding='utf-8')
    documents = loader.load()

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)

    vectorstore = FAISS.from_documents(texts, embedding=embedding_model)
    vectorstore.save_local(index_path)
    print("向量索引创建完成并已保存")
    return vectorstore

def Get_Prompt() -> PromptTemplate:
    """
    定义标准 RAG 问答提示模板
    """
    template = """请使用以下提供的文本内容来回答问题。
仅使用提供的文本信息，如果文本中没有相关信息，请回答"抱歉，提供的文本中没有这个信息"。

文本内容：
{context}

问题：{question}
回答：
"""
    return PromptTemplate.from_template(template)

def RAG_QA(question: str, vectorstore: FAISS, llm: ChatOpenAI) -> str:
    """
    执行基于检索的问答
    """
    retriever = vectorstore.as_retriever()
    docs = retriever.invoke(question)
    if not docs:
        return "抱歉，提供的文本中没有这个信息。"

    context = "\n\n".join([d.page_content for d in docs])

    prompt = Get_Prompt()
    chain = prompt | llm

    result = chain.invoke({"question": question, "context": context})
    return result.content.strip()

if __name__ == "__main__":
    llm, embedding_model = Init_Models()
    vectorstore = Build_Vectorstore()

    questions: list[str] = [
        "北京有什么著名的建筑？",
        "北京的气候有什么特点？",
        "北京有哪些现代化建筑？",
        "北京有哪些大学？",
        "上海是中国的首都吗？",
    ]

    print("\n现在可以开始提问啦！")
    for q in questions:
        print(f"\n问题：{q}")
        answer = RAG_QA(q, vectorstore, llm)
        print(f"回答：{answer}")
