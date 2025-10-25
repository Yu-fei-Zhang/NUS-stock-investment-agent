# NUS-stock-investment-agent

## SECTION 1 : PROJECT TITLE
A-share Investment Agent
![bc50cf633537c6bb99d10448f3f0b36d.png](Resource/bc50cf633537c6bb99d10448f3f0b36d.png)
## SECTION 2 : EXECUTIVE SUMMARY / PAPER ABSTRACT
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

## SECTION 3 : CREDITS / PROJECT CONTRIBUTION
| Official Full Name | Student ID | Work Items         | Email         |
|--------------------|-------------------------------|------------------------------------|--------------------------|
| Desmond Chua       | A1234567A                     | xxxxxxxxxxx yyyyyyyyyyy zzzzzzzzzzz | A1234567A@nus.edu.sg     |
| Chang Ye Han       | A1234567B                     | xxxxxxxxxxx yyyyyyyyyyy zzzzzzzzzzz | A1234567B@gmail.com      |
| Chee Jia Wei       | A1234567C                     | xxxxxxxxxxx yyyyyyyyyyy zzzzzzzzzzz | A1234567C@outlook.com    |
| Ganesh Kumar       | A1234567D                     | xxxxxxxxxxx yyyyyyyyyyy zzzzzzzzzzz | A1234567D@yahoo.com      |
| Jeanette Lim       | A1234567E                     | xxxxxxxxxxx yyyyyyyyyyy zzzzzzzzzzz | A1234567E@qq.com         |

## SECTION 4 : VIDEO OF SYSTEM MODELLING & USE CASE DEMO

## SECTION 5 : USER GUIDE
* clone repository to local by ```git clone https://github.com/Yu-fei-Zhang/NUS-stock-investment-agent.git```
* Install dependencies by ```pip install -r requirements.txt```
* Run the main script by ```python stock_agent/agent/agent.py```

## SECTION 6 : PROJECT REPORT / PAPER
* Executive Summary / Paper Abstract
* Sponsor Company Introduction (if applicable)
* Business Problem Background
* Market Research
* Project Objectives & Success Measurements
* Project Solution (To detail domain modelling & system design.)
* Project Implementation (To detail system development & testing approach.)
* Project Performance & Validation (To prove project objectives are met.)
* Project Conclusions: Findings & Recommendation
* Appendix of report: Project Proposal
* Appendix of report: Mapped System Functionalities against knowledge, techniques and skills of modular courses: MR, RS, CGS
* Appendix of report: Installation and User Guide
* Appendix of report: 1-2 pages individual project report per project member, including: Individual reflection of project journey: (1) personal contribution to group project (2) what learnt is most useful for you (3) how you can apply the knowledge and skills in other situations or your workplaces
* Appendix of report: List of Abbreviations (if applicable)
* Appendix of report: References (if applicable)
## SECTION 7 : MISCELLANEOUS
Refer to Github Folder: Resource
## System Design
### Overall

  ![1757317317557.jpg](Resource/1757317317557.jpg)

* An agent system usually consists of four main components: Orchestration, LLM, Memory and Tools. We'll introduce each component in detail below.
* **Orchestration**: The orchestration component is responsible for managing the overall workflow of the agent system. It coordinates the interactions between the LLM, memory, and tools to ensure that the agent can effectively process user inputs and generate appropriate responses. 
* **LLM**: The LLM component is the core of the agent system. It utilizes a large language model to understand and generate human-like text based on the input it receives. The LLM is responsible for interpreting user queries, generating responses, and making decisions based on the information available in memory and through tools.
* **Memory**: The memory component stores relevant information that the agent can use to inform its decisions and responses. This can include user profiles, historical data, and any other context that may be useful for the agent to reference when interacting with users.
* **Tools**: The tools component provides the agent with access to external resources and functionalities that can enhance its capabilities. This can include APIs for retrieving real-time stock data, executing trades, and performing technical analysis.

### Orchestration
We want to create an orchestration framework to conduct how the agent works by mimicking how a real trading team operates in secondary stock markets.
Specifically, we design a four-layer orchestration framework, including **User Profile processing**, **Stock Analysis**, **Investment Decision-Making I** and **Investment Decision-Making II**, every of which representing a real stage when trading team try to make their investment.

* **User Profile processing**: In this stage, the agent collects and processes the user's investment profile, which can be expressed as natural language or formated sheet. 
If the natural language is provided, the agent will extract the key information by interacting with LLM. Eventually, all information will be transferred to a structured data and will be stored in short-term memory for reference in the following steps.
What the agent collects mainly concentrated on three aspects: investment goal, risk tolerance and financial condition. The agent will continue to ask the user for more information if some compulsory data is not provided. Then, the agent will summarize the user's investment profile and confirm with the user before moving to the next stage.
  * **Investment goal**: The agent will analyze their investment goals, including short-term investment goal, long-term investment goal and expected earnings. This information helps the agent understand the user's objectives and tailor its recommendations accordingly.
  * **Risk tolerance**: The agent will assess the user's risk tolerance level about their comfort level with market fluctuations and acceptance of loss. This helps the agent tailor its recommendations to align with the user's risk profile.
  * **Financial condition**: The agent will acquire the specific principal the user want to invest, which helps the agent to make investment decisions within the user's financial capacity.

* **Stock Analysis**: In this stage, our agent conducts a comprehensive analysis of the stock market to generate an assessment report for every stock. The agent will utilize various tools to gather and analyze data, including market news analysis, technical analysis, and fundamental analysis. The results of the stock analysis will be stored in long-term memory for reference in the following stages.
We try to use the real assessment report as created by stock investment analyzer. However, a real assessment report usually contains tens of thousands of words in English, which exceeds the capacity of the context the LLM can solve once. In out design, we need to extract the most significant points expressed in every report so that LLM can analyze multiple stocks comprehensively at one time.
The assessment report for one stock contains the following aspects:
  * **Valuation Analysis**: The agent will evaluate the stock's valuation using various metrics to generate absolute and relative evaluation. This helps the agent determine whether the stock is overvalued or undervalued compared to its historical averages and industry peers.
  * **Advantage Analysis**: The agent will identify the company's internal **competitive advantages** and **industry advantages**, such as market position, brand strength unique products or services and industry development space. This helps the agent assess the company's ability to maintain its market share and profitability over time.
  * **Risk Analysis**: The agent will identify the potential risks associated with the stock, including **internal risks** (e.g., financial health, management quality) and **external risks** (e.g., market competition, regulatory changes). This helps the agent understand the factors that could negatively impact the stock's performance.

* **Investment Decision-Making I**: In this stage, the agent will make investment decisions based on the user's investment profile and the stock analysis results stored in memory. 
The agent will utilize the LLM to process the information and generate **investment plans**. The agent will consider various factors, including the user's investment goals, risk tolerance, and financial condition, as well as the stock's valuation, advantages, and risks.
An investment plan typically includes the following components:
  * **Stock Selection**: The agent will select a portfolio of stocks that align with the user's investment profile and the stock analysis results.
  * **Position Sizing**: The agent will determine the appropriate position size for each stock in the portfolio based on the user's financial condition and risk tolerance. This helps ensure that the user does not overexpose themselves to any single stock or sector.
  * **Entry and Exit Points**: The agent will identify optimal entry and exit points for each stock based on technical analysis and market conditions. This helps maximize potential returns while minimizing risks.

* **Investment Decision-Making II**: At this stage, the agent will formulate a more detailed trading strategy, enabling users to execute trades simply by following it. Specifically, the agent will determine concrete trading plans for each stock included in the investment scheme.
To achieve users' expected returns, the trading plan must be implemented strictly. Meanwhile, the agent will continuously monitor market dynamics and make necessary adjustments to the trading plan, ensuring it remains aligned with both the user's investment profile and the results of stock analysis.
An executed trading plan illustrates the following two rules:
  * **Buying-in Rules**: The agent will determine the specific conditions, including the related data indexes, under which to buy a stock and how much should be invested.
  * **Selling-out Rules**: The agent will determine the specific selling points when earnings or losses reach a certain threshold.

### LLM
We want the user to have freedom to choose the LLM they prefer. Therefore, we design the LLM component to be easily replaceable.

### Memory


The memory module is designed to support both **long-term knowledge retention** and **short-term contextual awareness**, enabling the investment agent to make personalized and context-aware decisions.  

### Long-Term Memory  
We adopt a hybrid storage approach:  

- **Relational Database**  
  Stores structured stock analysis results (e.g., valuation, risk, recommendations).  
  Data is updated daily and kept for several days, supporting historical queries and validation.  

- **Vector Database**  
  Stores unstructured documents (e.g., market news, analyst reports).  
  Texts are transformed into vector embeddings to enable semantic similarity search, ensuring the agent can retrieve relevant information beyond keyword matching.  

This design allows efficient retrieval of both structured financial metrics and context-rich textual information.  

### Short-Term Memory  
We use a **key-value database** to store:  

- **User Investment Profile** (goals, risk tolerance, financial condition).  
- **Session Context** (unanswered questions, workflow progress, last executed step).  

STM ensures that the agent’s recommendations are always aligned with user objectives while maintaining a smooth, stateful interaction.  
Data is session-based and refreshed frequently to avoid stale context.  

### Workflow  
1. **Retrieval**: Load user profile (STM) + relevant stock data (LTM).  
2. **Reasoning**: LLM integrates memory outputs with user queries.  
3. **Update**: STM updated per interaction, LTM updated daily/continuously.  

### Benefits  
- **Efficiency**: Fast access to user-specific context.  
- **Scalability**: Hybrid design supports structured and unstructured data.  
- **Personalization**: Tailored investment advice through STM.  
- **Robustness**: Clear separation of short- and long-term memory.  

### Tools
Tools are essential for enhancing the capabilities of the investment agent. We have integrated several tools to provide the agent with access to real-time data and functionalities that are crucial for making informed investment decisions. The tools we have integrated include:
* **Real-Time Stock Data API**: This tool allows the agent to retrieve up-to-date stock price data, market trends, and other relevant financial information necessary for analysis and decision-making.
* **Trading API**: This tool enables the agent to execute trades on behalf of the user, including buying and selling stocks based on the investment decisions made by the agent.
* **Technical Analysis Tool**: This tool provides the agent with the ability to perform technical analysis on stock price data, including calculating various technical indicators and generating charts to visualize price trends.
* **Fundamental Analysis Tool**: This tool allows the agent to analyze a company's financial statements and other fundamental data to assess its financial health and performance.
* **Market News Analysis Tool**: This tool enables the agent to analyze market news and sentiment to identify potential factors that could impact stock prices.
* **Risk Assessment Tool**: This tool helps the agent evaluate the risks associated with different stocks and investment strategies, allowing it to make recommendations that align with the user's risk tolerance.
* **Portfolio Optimization Tool**: This tool assists the agent in optimizing the user's investment portfolio by analyzing asset allocation and diversification strategies to maximize returns while minimizing risks.
* **Backtesting Tool**: This tool allows the agent to test investment strategies using historical data to evaluate their performance and effectiveness before implementing them in real-time trading.
* **Performance Monitoring Tool**: This tool enables the agent to monitor the performance of the user's investment portfolio in real-time, providing insights and alerts on significant changes or events that may require attention.
* **Compliance and Regulatory Tool**: This tool ensures that the agent's investment activities comply with relevant regulations and guidelines, helping to mitigate legal and regulatory risks.
* **User Feedback Tool**: This tool allows the agent to collect and analyze user feedback on its performance and recommendations, enabling continuous improvement and adaptation to the user's preferences and needs.
