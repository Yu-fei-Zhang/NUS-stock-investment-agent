from __future__ import annotations

from langchain.agents import ConversationalChatAgent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI

from stock_agent.agent.orchestration.OrchestratorPrompt import OrchestrationPrompt

llm = ChatOpenAI(
    temperature=0.9,
    api_key="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"
)
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)
tools = []
agent = ConversationalChatAgent.from_llm_and_tools(llm=llm, tools=tools, system_message=OrchestrationPrompt.ROLE_PROMPT + OrchestrationPrompt.STAGE1_PROMPT
                                                   + OrchestrationPrompt.STAGE2_PROMPT + OrchestrationPrompt.STAGE3_PROMPT + OrchestrationPrompt.STAGE4_PROMPT)
agent_executor = AgentExecutor(agent=agent,memory=memory ,tools=tools, verbose=True)
agent_executor.invoke({"input": "你好，我想向你获取股票投资的建议"})

