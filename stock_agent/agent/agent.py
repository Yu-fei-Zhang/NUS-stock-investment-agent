from __future__ import annotations

from langchain.agents import ConversationalChatAgent, AgentExecutor
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI

from stock_agent.memory.Short_termMemory import RedisChatMemory
from stock_agent.agent.orchestration.OrchestratorPrompt import OrchestrationPrompt

llm = ChatOpenAI(
    temperature=0.9,
    api_key="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"
)
memory = RedisChatMemory(
    memory_key="chat_history",
    return_messages=True
)
tools = []
agent = ConversationalChatAgent.from_llm_and_tools(llm=llm, tools=tools, system_message=OrchestrationPrompt.ROLE_PROMPT + OrchestrationPrompt.STAGE1_PROMPT
                                                   + OrchestrationPrompt.STAGE2_PROMPT + OrchestrationPrompt.STAGE3_PROMPT + OrchestrationPrompt.STAGE4_PROMPT)
agent_executor = AgentExecutor(agent=agent,memory=memory ,tools=tools, verbose=True)

print("✅ 股票投资咨询助手已启动！输入 '退出' 可结束对话。")
while True:
    # 2.1 获取用户当前输入
    user_input = input("\n你：")

    # 2.2 终止逻辑：用户输入“退出”时结束对话
    if user_input.strip().lower() in ["退出", "结束", "bye"]:
        print("助手：感谢咨询！投资有风险，入市需谨慎，再见～")
        break

    # 2.3 调用 Agent 执行器：传入当前输入 + 自动读取历史记忆
    try:
        response = agent_executor.invoke(
            input={"input": user_input},  # 每次仅需传入当前输入，memory 会自动注入历史
            return_only_outputs=True  # 仅返回 Agent 的最终响应（简化输出）
        )

        # 2.4 打印 Agent 响应
        print(f"助手：{response['output']}")

    # 2.5 异常处理（如 API 调用失败、密钥错误等）
    except Exception as e:
        print(f"❌ 对话出错：{str(e)[:100]}（请检查 API 密钥或网络）")
        continue

