from abc import ABC, abstractmethod

from langchain.chains.llm import LLMChain
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory, ChatMessageHistory
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import OpenAI, ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter

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