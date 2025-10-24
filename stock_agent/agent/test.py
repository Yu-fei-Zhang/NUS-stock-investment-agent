# python
# 文件: server.py
from flask import Flask, request, jsonify, render_template_string, Response
import os
import time
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

# 初始化 LLM 与 AgentExecutor
OPENAI_API_KEY = "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"
llm = ChatOpenAI(temperature=0, api_key=OPENAI_API_KEY, model="gpt-4o", streaming=True)  # 开启streaming
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
tools = [a_share_random_industry_picks_tool, a_share_market_data_tool, a_share_company_news_tool,
         a_share_fundamentals_tool]

agent = ConversationalChatAgent.from_llm_and_tools(
    llm=llm,
    tools=tools,
    system_message=OrchestrationPrompt.ROLE_PROMPT + OrchestrationPrompt.STAGE1_PROMPT
                   + OrchestrationPrompt.STAGE2_PROMPT + OrchestrationPrompt.STAGE3_PROMPT + OrchestrationPrompt.STAGE4_PROMPT
)
agent_executor = AgentExecutor(agent=agent, memory=memory, tools=tools, verbose=False)

# 前端页面（含流式输出+加载动画）
PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Stock Investment Advisor</title>
  <style>
    :root {
      --primary: #2563eb;
      --secondary: #f3f4f6;
      --text: #1f2937;
      --user-bg: #e0f2fe;
      --bot-bg: #f9fafb;
      --shadow: rgba(0, 0, 0, 0.05);
      --border: #e5e7eb;
    }
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      max-width: 850px;
      margin: 2rem auto;
      padding: 0 1rem;
      color: var(--text);
      background-color: #f9fafb;
    }
    h1 {
      color: var(--primary);
      text-align: center;
      margin-bottom: 1.5rem;
      font-size: 1.8rem;
      font-weight: 600;
    }
    #chat {
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.5rem;
      height: 70vh;
      overflow-y: auto;
      background-color: white;
      box-shadow: 0 2px 10px var(--shadow);
    }
    .msg {
      margin: 0.8rem 0;
      padding: 0.8rem;
      border-radius: 8px;
      max-width: 80%;
      line-height: 1.6;
    }
    .user {
      background-color: var(--user-bg);
      color: var(--text);
      margin-left: auto;
      box-shadow: 0 1px 3px var(--shadow);
    }
    .bot {
      background-color: var(--bot-bg);
      color: var(--text);
      margin-right: auto;
      box-shadow: 0 1px 3px var(--shadow);
    }
    .loading {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: var(--primary);
    }
    .loading .spinner {
      width: 16px;
      height: 16px;
      border: 2px solid var(--primary);
      border-top-color: transparent;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    #inputBox {
      display: flex;
      gap: 0.5rem;
      margin-top: 1.5rem;
    }
    textarea {
      flex: 1;
      height: 3.5rem;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0.8rem;
      font-size: 0.95rem;
      resize: none;
      transition: border 0.3s;
    }
    textarea:focus {
      border-color: var(--primary);
      outline: none;
    }
    button {
      background-color: var(--primary);
      color: white;
      border: none;
      border-radius: 6px;
      padding: 0 1.2rem;
      cursor: pointer;
      font-size: 0.95rem;
      transition: background-color 0.3s;
    }
    button:hover {
      background-color: #1d4ed8;
    }
    button:disabled {
      background-color: #cbd5e1;
      cursor: not-allowed;
    }
    .msg-header {
      font-weight: 600;
      margin-bottom: 0.3rem;
      font-size: 0.9rem;
    }
    .user .msg-header {
      color: var(--primary);
    }
    .bot .msg-header {
      color: #6b7280;
    }
    .bot ul {
      margin-left: 1.5rem;
      margin-top: 0.3rem;
    }
    .bot li {
      margin-bottom: 0.2rem;
    }
  </style>
</head>
<body>
  <h1>Stock Investment Advisor</h1>
  <div id="chat"></div>
  <div id="inputBox">
    <textarea id="msg" placeholder="Type your question" rows="3"></textarea>
    <button id="send">Send</button>
  </div>

  <script>
    const chat = document.getElementById('chat');
    const msgInput = document.getElementById('msg');
    const sendBtn = document.getElementById('send');
    let currentBotMsg = null; // 用于保存当前正在流式输出的bot消息容器

    function formatAdvisorText(text) {
      return text.replace(/(\d+)\. (.*?)(?=\d+\. |$)/g, (match, num, content) => {
        return `<li><strong>${num}.</strong> ${content}</li>`;
      }).replace(/^((?!<li>).)+$/, (para) => {
        return `<p>${para}</p>`;
      }).replace(/^<li>/mg, '<ul><li>').replace(/<\/li>$/mg, '</li></ul>');
    }

    function appendMessage(who, text, isLoading = false, isStream = false) {
      const div = document.createElement('div');
      div.className = 'msg ' + who;

      const header = document.createElement('div');
      header.className = 'msg-header';
      header.textContent = who === 'user' ? 'You: ' : 'Advisor: ';

      const content = document.createElement('div');
      content.className = 'msg-content';
      if (who === 'bot') {
        if (isLoading) {
          content.innerHTML = `
            <div class="loading">
              <div class="spinner"></div>
              <span>Processing your request...</span>
            </div>
          `;
        } else if (isStream) {
          content.innerHTML = text;
        } else {
          content.innerHTML = formatAdvisorText(text);
        }
      } else {
        content.textContent = text;
      }

      div.appendChild(header);
      div.appendChild(content);
      chat.appendChild(div);
      chat.scrollTop = chat.scrollHeight;
      return div;
    }

    async function sendMessage() {
      const text = msgInput.value.trim();
      if (!text) return;
      appendMessage('user', text);
      msgInput.value = '';
      sendBtn.disabled = true;

      // 显示加载状态
      const loadingMsg = appendMessage('bot', '', true);

      try {
        // 发起流式请求
        const response = await fetch('/stream-chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });

        // 读取流式响应
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let streamContent = '';

        // 先移除加载提示，准备流式输出容器
        chat.removeChild(loadingMsg);
        currentBotMsg = appendMessage('bot', '', false, true);

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          streamContent += chunk;
          // 实时更新UI
          currentBotMsg.querySelector('.msg-content').innerHTML = formatAdvisorText(streamContent);
          chat.scrollTop = chat.scrollHeight;
        }
      } catch (e) {
        if (currentBotMsg) chat.removeChild(currentBotMsg);
        appendMessage('bot', 'ERROR：' + e.message);
      } finally {
        sendBtn.disabled = false;
        currentBotMsg = null;
      }
    }

    sendBtn.addEventListener('click', sendMessage);
    msgInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(PAGE)

@app.route("/stream-chat", methods=["POST"])
def stream_chat_endpoint():
    payload = request.get_json() or {}
    message = payload.get("message", "").strip()
    if not message:
        return jsonify({"error": "empty message"}), 400

    def generate_stream():
        try:
            # 流式调用Agent
            for chunk in agent_executor.stream(
                input={"input": message},
                config={"return_only_outputs": True}
            ):
                yield chunk["output"]
        except Exception as e:
            yield f"Error: {str(e)}"

    return Response(generate_stream(), mimetype='text/plain')

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)