from langchain.agents import initialize_agent, AgentType
from agent.llm import get_llm
from agent.memory import get_stm
from agent.tools import get_tools


class AgentOrchestrator:
    def __init__(self, model_name="openai"):
        self.llm = get_llm(model_name=model_name)
        self.tools = get_tools()
        self.memory = get_stm()
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True,
        )

    def run(self, user_input):
        # 统一入口，自动完成四阶段决策流程
        return self.agent.run(user_input)
