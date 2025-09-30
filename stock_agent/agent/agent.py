from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from typing import Optional, Any

import search_tool
from langchain.agents import initialize_agent, AgentType, create_tool_calling_agent, ConversationalChatAgent
from langchain.agents.conversational.output_parser import ConvoOutputParser
from langchain.memory import ConversationBufferMemory
from langchain_community.tools import TavilySearchResults
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.prompts import BasePromptTemplate, ChatPromptTemplate, SystemMessagePromptTemplate, \
    MessagesPlaceholder, HumanMessagePromptTemplate
from langchain_core.tools import BaseTool

from langchain.agents.agent import AgentOutputParser, AgentExecutor
from langchain.agents.conversational.prompt import PREFIX, SUFFIX
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI


class StockAgent(ConversationalChatAgent, ABC):

    @classmethod
    def create_prompt(
            cls,
            tools: Sequence[BaseTool],
            system_message: str = PREFIX,
            human_message: str = SUFFIX,
            input_variables: Optional[list[str]] = None,
            output_parser: Optional[BaseOutputParser] = None,
    ) -> BasePromptTemplate:
        """Create a prompt for the agent.

        Args:
            tools: The tools to use.
            system_message: The system message to use.
                Defaults to the PREFIX.
            human_message: The human message to use.
                Defaults to the SUFFIX.
            input_variables: The input variables to use. Defaults to None.
            output_parser: The output parser to use. Defaults to None.

        Returns:
            A PromptTemplate.
        """
        tool_strings = "\n".join(
            [f"> {tool.name}: {tool.description}" for tool in tools],
        )
        tool_names = ", ".join([tool.name for tool in tools])
        _output_parser = output_parser or cls._get_default_output_parser()
        format_instructions = human_message.format(
            format_instructions=_output_parser.get_format_instructions(),
        )
        final_prompt = format_instructions.format(
            tool_names=tool_names,
            tools=tool_strings,
        )
        if input_variables is None:
            input_variables = ["input", "chat_history", "agent_scratchpad"]
        messages = [
            SystemMessagePromptTemplate.from_template(system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template(final_prompt),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
        return ChatPromptTemplate(input_variables=input_variables, messages=messages)

    @classmethod
    def _get_default_output_parser(cls, **kwargs: Any) -> AgentOutputParser:
        return ConvoOutputParser(**kwargs)

    @property
    def observation_prefix(self) -> str:
        """Prefix to append the observation with."""

    @property
    def llm_prefix(self) -> str:
        """Prefix to append the LLM call with."""



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

