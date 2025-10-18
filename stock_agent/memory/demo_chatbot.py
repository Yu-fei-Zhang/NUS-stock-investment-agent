import os
from langchain.chains import ConversationChain
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_openai import ChatOpenAI
from Short_termMemory import RedisChatMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

# ① LLM
llm = ChatOpenAI(
    temperature=0.9,
    api_key="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"
)

# ② Redis 历史
history = RedisChatMessageHistory(
    session_id="user42",
    url="redis://localhost:6379/0",
    key_prefix="chat:msg:"
)

# ③ 记忆组件（return_messages=True 关键）
memory = RedisChatMemory(
    chat_memory=history,
    redis_url="redis://localhost:6379/0",
    return_messages=True
)

# ④ 显式 prompt：把 history 拼进去
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    MessagesPlaceholder(variable_name="history"),  # ← 整条消息列表
    ("human", "{input}")
])

# ⑤ 组装 chain
chain = ConversationChain(
    llm=llm,
    memory=memory,
    prompt=prompt          # 关键：告诉 chain 怎么拼历史
)

# ⑥ 开聊（用 invoke 消除弃用警告）
out1 = chain.invoke({"input": "苏州天气如何？"})
print("AI:", out1["response"])

out2 = chain.invoke({"input": "我问的是哪个城市？"})
print("AI:", out2["response"])

out1 = chain.invoke({"input": "我刚问的是苏州的什么？"})
print("AI:", out1["response"])

