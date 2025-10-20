from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
import os
from typing import List, Union



def Init_Models() -> tuple[ChatOpenAI, OpenAIEmbeddings]:
    """
    初始化大模型与嵌入模型
    """
    llm = ChatOpenAI(model="gpt-5", temperature=1)
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")
    return llm, embedding_model


def Load_Documents(
    paths: Union[str, List[str]],
) -> list:
    """
    支持加载单个文件、多个文件或文件夹中所有文本文件
    """
    all_docs = []

    # 如果传入单个路径
    if isinstance(paths, str):
        if os.path.isdir(paths):
            # 加载文件夹内所有 .txt 文件
            file_list = [
                os.path.join(paths, f)
                for f in os.listdir(paths)
                if f.endswith(".txt")
            ]
        else:
            file_list = [paths]
    else:
        file_list = paths

    for file_path in file_list:
        if not os.path.exists(file_path):
            print(f"跳过不存在的文件：{file_path}")
            continue

        loader = TextLoader(file_path, encoding="utf-8")
        docs = loader.load()
        for d in docs:
            d.metadata["source"] = os.path.basename(file_path)
        all_docs.extend(docs)

    if not all_docs:
        raise ValueError("未找到任何可用的文档。")

    print(f"成功加载 {len(all_docs)} 个文档片段，来自 {len(file_list)} 个文件。")
    return all_docs


def Build_Vectorstore(
    file_path: Union[str, List[str]] = "../../Resource/docs",
    index_path: str = "faiss_index"
) -> FAISS:
    """
    构建或加载 FAISS 向量数据库，支持多文件或文件夹
    """
    llm, embedding_model = Init_Models()

    if os.path.exists(index_path):
        print("已加载本地向量索引")
        return FAISS.load_local(index_path, embedding_model, allow_dangerous_deserialization=True)

    print("正在创建向量索引...")
    documents = Load_Documents(file_path)

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


def RAG_QA(question: str, vectorstore: FAISS, llm: ChatOpenAI, k: int = 8) -> str:
    """
    执行基于检索的问答
    """
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    docs = retriever.invoke(question)
    if not docs:
        return "抱歉，提供的文本中没有这个信息。"

    context = "\n\n".join([f"来源({d.metadata.get('source','未知')}): {d.page_content}" for d in docs])

    prompt = Get_Prompt()
    chain = prompt | llm

    result = chain.invoke({"question": question, "context": context})
    return result.content.strip()


if __name__ == "__main__":
    llm, embedding_model = Init_Models()

    vectorstore = Build_Vectorstore(file_path="../../Resource/docs")
    '''
    vectorstore = Build_Vectorstore(file_path=[
        "../../Resource/docs/beijing.txt",
        "../../Resource/docs/shanghai.txt"
    ])
    '''

    questions = [
        "北京有什么著名的建筑？",
        "北京和上海分别有什么大学？",
        "上海是中国的首都吗？",
    ]

    for q in questions:
        print(f"\n问题：{q}")
        answer = RAG_QA(q, vectorstore, llm)
        print(f"回答：{answer}")
