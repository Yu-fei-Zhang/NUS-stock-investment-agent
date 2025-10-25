from flask import Flask, request, jsonify, render_template, session, redirect, url_for, Response
import os
import secrets
from datetime import timedelta
from langchain.memory import ConversationBufferMemory
from langchain.agents import ConversationalChatAgent, AgentExecutor
from langchain_openai import ChatOpenAI
from stock_agent.tools.tools_CN_A_share import (
    a_share_random_industry_picks_tool,
    a_share_market_data_tool,
    a_share_company_news_tool,
    a_share_fundamentals_tool,
)
from stock_agent.agent.orchestration.OrchestratorPrompt import OrchestrationPrompt

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# 简单的用户数据库（实际应用中应使用真实数据库）
USERS = {
    "demo": "demo123",  # username: password
    "admin": "admin123"
}

# 初始化 LLM 与 AgentExecutor
OPENAI_API_KEY = ""

# 为每个用户维护独立的 memory 和 agent
user_agents = {}


def get_user_agent(username):
    """获取或创建用户的 agent executor"""
    if username not in user_agents:
        llm = ChatOpenAI(temperature=0, api_key=OPENAI_API_KEY, model="gpt-4o", streaming=True)
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        tools = [
            a_share_random_industry_picks_tool,
            a_share_market_data_tool,
            a_share_company_news_tool,
            a_share_fundamentals_tool
        ]

        agent = ConversationalChatAgent.from_llm_and_tools(
            llm=llm,
            tools=tools,
            system_message=OrchestrationPrompt.ROLE_PROMPT + OrchestrationPrompt.STAGE1_PROMPT
                           + OrchestrationPrompt.STAGE2_PROMPT + OrchestrationPrompt.STAGE3_PROMPT
                           + OrchestrationPrompt.STAGE4_PROMPT
        )
        user_agents[username] = AgentExecutor(agent=agent, memory=memory, tools=tools, verbose=False)

    return user_agents[username]


@app.route("/")
def index():
    if 'username' in session:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))


@app.route("/login")
def login():
    if 'username' in session:
        return redirect(url_for('chat'))
    return render_template('login.html')


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if username in USERS and USERS[username] == password:
        session['username'] = username
        session.permanent = True
        return jsonify({"success": True})

    return jsonify({"success": False, "error": "Invalid credentials"}), 401


@app.route("/logout")
def logout():
    username = session.get('username')
    if username and username in user_agents:
        del user_agents[username]
    session.clear()
    return redirect(url_for('login'))


@app.route("/chat")
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', username=session['username'])


@app.route("/stream-chat", methods=["POST"])
def stream_chat_endpoint():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    payload = request.get_json() or {}
    message = payload.get("message", "").strip()

    if not message:
        return jsonify({"error": "empty message"}), 400

    username = session['username']
    agent_executor = get_user_agent(username)

    def generate_stream():
        try:
            for chunk in agent_executor.stream(
                    input={"input": message},
                    config={"return_only_outputs": True}
            ):
                yield chunk.get("output", "")
        except Exception as e:
            yield f"Error: {str(e)}"

    return Response(generate_stream(), mimetype='text/plain')


@app.route("/clear-history", methods=["POST"])
def clear_history():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    username = session['username']
    if username in user_agents:
        del user_agents[username]

    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)