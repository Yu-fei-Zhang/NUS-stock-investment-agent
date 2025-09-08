# NUS-stock-investment-agent

## Background
* In real secondary stock markets, private investors often face challenges in making appropriate decisions to get their expected earnings
due to multiple reasons:
  1. **Lack of instant knowledge in stock markets**
     * it's hard for private investors to keep up with the fast-changing factors that influence stock prices, such as market news, economic indicators, and company performance.
     * Private investors is inclined to be affected by the market hype and other inappropriate factors, leading to irrational investment decisions.
  2. **Internal behavioral flaws in every private investor**
     * Private investors are inclined to make investment based on emotions, biases, and herd mentality rather than professional analysis.
     * Emotional reactions to market fluctuations can result in impulsive selling, rather than following a well-thought-out and long-term investment strategy.
  3. **Limited personal capacity**
     * Private investors often lack the time, resources, and expertise to conduct thorough research and analysis of stocks, compared with other professional financial institutions.
* To address these challenges, we have developed an LLM-powered investment agent, simulating professionals' behaviors in secondary stock markets, to assist users in automating their investment strategies and stock trading activities. 
If the agent get a user's investment profile, including investment goal and risk tolerance, it can help the user to make investment decisions and execute trades on their behalf t achieve the expected earnings.

## System Design
### Overall

  ![1757317317557.jpg](1757317317557.jpg)

* An agent system usually consists of four main components: Orchestration, LLM, Memory and Tools. We'll introduce each component in detail below.
* **Orchestration**: The orchestration component is responsible for managing the overall workflow of the agent system. It coordinates the interactions between the LLM, memory, and tools to ensure that the agent can effectively process user inputs and generate appropriate responses. 
* **LLM**: The LLM component is the core of the agent system. It utilizes a large language model to understand and generate human-like text based on the input it receives. The LLM is responsible for interpreting user queries, generating responses, and making decisions based on the information available in memory and through tools.
* **Memory**: The memory component stores relevant information that the agent can use to inform its decisions and responses. This can include user profiles, historical data, and any other context that may be useful for the agent to reference when interacting with users.
* **Tools**: The tools component provides the agent with access to external resources and functionalities that can enhance its capabilities. This can include APIs for retrieving real-time stock data, executing trades, and performing technical analysis.

### Orchestration
We want to create an orchestration framework to conduct how the agent works by mimicking how a real trading team operates in secondary stock markets.
Specifically, we design a four-layer orchestration framework, including **User Profile processing**, **Stock Analysis**, **Investment Decision-Making** and **Investment Decision Execution**, every of which representing a real stage when trading team try to make their investment.

* **User Profile processing**: In this stage, the agent collects and processes the user's investment profile, which can be expressed as natural language or formated sheet. 
If the natural language is provided, the agent will extract the key information by interacting with LLM. Eventually, all information will be transferred to a structured data and will be stored in short-term memory for reference in the following steps.
What the agent collects mainly concentrated on three aspects: investment goal, risk tolerance and financial condition. The agent will continue to ask the user for more information if some compulsory data is not provided. Then, the agent will summarize the user's investment profile and confirm with the user before moving to the next stage.
  * **Investment goal**: The agent will analyze their investment goals, including short-term investment goal, long-term investment goal and expected earnings. This information helps the agent understand the user's objectives and tailor its recommendations accordingly.
  * **Risk tolerance**: The agent will assess the user's risk tolerance level about their comfort level with market fluctuations and acceptance of loss. This helps the agent tailor its recommendations to align with the user's risk profile.
  * **Financial condition**: The agent will acquire the specific principal the user want to invest, which helps the agent to make investment decisions within the user's financial capacity.

* **Stock Analysis**: In this stage, the agent conducts a comprehensive analysis of the stock market to identify potential investment opportunities. The agent will leverage various tools to gather and analyze data, including:
  * **Market News Analysis**: The agent will use a news analysis tool to monitor and analyze relevant market news and events that may impact stock prices. This helps the agent stay informed about market trends and make timely investment decisions.
  * **Technical Analysis**: The agent will utilize technical analysis tools to evaluate historical price patterns, trading volumes, and other technical indicators. This helps the agent identify potential entry and exit points for trades.
  * **Fundamental Analysis**: The agent will employ fundamental analysis tools to assess the financial health and performance of companies. This includes analyzing financial statements, earnings reports, and other key metrics to determine the intrinsic value of stocks.

