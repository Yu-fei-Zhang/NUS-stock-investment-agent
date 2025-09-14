from agent.orchestrator import AgentOrchestrator

if __name__ == '__main__':
    # Initialize the agent with OpenAI LLM
    agent = AgentOrchestrator(model_name="openai")
    # Example user input (English)
    user_input = "I want to invest in technology stocks, target annualized return 10%, can tolerate medium risk, investment principal 100,000 RMB."
    result = agent.run(user_input)
    print(result)
    print("Intelligent investment agent process completed.")
