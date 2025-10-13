from __future__ import annotations

from langchain.agents import ConversationalChatAgent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI

from stock_agent.agent.orchestration.OrchestratorPrompt import OrchestrationPrompt

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)
tools = []
agent = ConversationalChatAgent.from_llm_and_tools(llm=llm, tools=tools, system_message=OrchestrationPrompt.ROLE_PROMPT + OrchestrationPrompt.STAGE1_PROMPT
                                                   + OrchestrationPrompt.STAGE2_PROMPT + OrchestrationPrompt.STAGE3_PROMPT + OrchestrationPrompt.STAGE4_PROMPT)
agent_executor = AgentExecutor(agent=agent,memory=memory ,tools=tools, verbose=True)

