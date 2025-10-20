import random

from langchain.agents import ConversationalChatAgent, AgentExecutor
from langchain.tools import tool
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from stock_agent.memory.Short_termMemory import RedisChatMemory


class FieldInfo(BaseModel):
    a :int = Field(description="第1个参数")
@tool(name_or_callable="one_number_transform",description="one_number_transform",args_schema=FieldInfo,return_direct=True)
def add_number(a:int)-> str:
    """两个整数相加"""
    return "a * 0.5"

llm = ChatOpenAI(
    temperature=0.9,
    api_key="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",
    model="gpt-4o"
)

tools = [add_number]

agent = ConversationalChatAgent.from_llm_and_tools(llm=llm, tools=tools, system_message="you are a helpful assistant.")


history = RedisChatMessageHistory(
    session_id=str(random.randint(0, 99999999)),
    url="redis://localhost:6379/0",
    key_prefix="chat:msg:"
)

memory = RedisChatMemory(
    chat_memory=history,
    redis_url="redis://localhost:6379/0",
    return_messages=True,
    memory_key="chat_history"
)

agent_executor = AgentExecutor(agent=agent,memory=memory ,tools=tools, verbose=True)

response = agent_executor.invoke(
            input={"input": "please help me to transform number 5 by calling the tool"},  # 每次仅需传入当前输入，memory 会自动注入历史
            return_only_outputs=True  # 仅返回 Agent 的最终响应（简化输出）
        )
print(response['output'])