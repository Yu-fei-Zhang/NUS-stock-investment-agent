import search_tool
from langchain.agents import initialize_agent, AgentType, create_tool_calling_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain_community.tools import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)
agent_executor = initialize_agent(
    tools=[search_tool],
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True
)
query1="北京明天的天气怎么样？"
result1 = agent_executor.invoke(query1)
print(f"查询结果: {result1}")
query2="上海呢"
result2=agent_executor.invoke(query2)
print(f"分析结果: {result2}")

# 自定义agent提示词模板
search = TavilySearchResults(max_results=2)
tools = [search]
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个有用的助手，可以回答问题并使用工具。"),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])
# 7.创建Agent对象
agent = create_tool_calling_agent(llm, tools, prompt)
# 8.创建AgentExecutor执行器对象(通过源码可知，memory参数声明在AgentExecutor父类中)
agent_executor = AgentExecutor(agent=agent,memory=memory ,tools=tools, verbose=True)