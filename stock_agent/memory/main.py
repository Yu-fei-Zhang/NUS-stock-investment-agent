from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from typing import Optional, Any

import search_tool
from langchain.agents import initialize_agent, AgentType, create_tool_calling_agent, ConversationalChatAgent, \
    create_react_agent
from langchain.agents.conversational.output_parser import ConvoOutputParser
from langchain.memory import ConversationBufferMemory
from langchain_community.tools import TavilySearchResults
from langchain_core.prompts import PromptTemplate, BasePromptTemplate, ChatPromptTemplate
from langchain_core.tools import BaseTool

from langchain.agents.agent import AgentOutputParser, AgentExecutor
from langchain.agents.conversational.prompt import FORMAT_INSTRUCTIONS, PREFIX, SUFFIX
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI

from stock_agent.agent.agent import StockAgent

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

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
agent = StockAgent.from_llm_and_tools(llm, tools, prompt=prompt, verbose=True)
# 8.创建AgentExecutor执行器对象(通过源码可知，memory参数声明在AgentExecutor父类中)
agent_executor = AgentExecutor(agent=agent,memory=memory ,tools=tools, verbose=True)
