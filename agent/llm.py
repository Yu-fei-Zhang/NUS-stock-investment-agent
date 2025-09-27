from typing import Any, Optional
import asyncio
from langchain_core.messages import ChatMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, \
    AIMessagePromptTemplate, MessagesPlaceholder, FewShotPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import (
    SystemMessage,  # 系统消息：定义助手的角色和行为准则
    HumanMessage,   # 人类消息：用户输入的内容
    AIMessage       # AI消息：模型的回复内容
)
from abc import ABC
from langchain.prompts import PromptTemplate

# BaseLLM 是所有 LLM（大语言模型）组件的抽象基类，定义了系统提示词、模型实例、对话历史等通用属性和接口。
# 子类需实现对话历史的查询和构建方法。
class BaseLLM(ABC):
    system_prompt: SystemMessage  # 系统提示词，定义模型行为和角色
    chat_model: Any               # 底层 LLM 聊天模型实例（如 OpenAI、ChatOpenAI 等）
    message_history: list    # 对话历史记录，存储用户和模型的交互内容

    def __init__(self, system_prompt: Optional[SystemMessage] = None, chat_model: Optional[Any] = None):
        """
        初始化 BaseLLM。
        :param system_prompt: 系统提示词，定义助手角色和行为
        :param chat_model: 底层 LLM 聊天模型实例
        """
        self.system_prompt = system_prompt or ""
        self.dialogue_history = []  # 用于存储对话历史
        if chat_model is not None:
            self.chat_model = chat_model

    def chat(self, input: HumanMessage) -> AIMessage:
        """
        与 LLM 聊天，自动记录对话历史。
        :param input: 用户输入消息
        :return: LLM 回复消息
        """
        self.message_history.append(input)
        response = self.chat_model(self.to_message_list())
        return response

    def add_human_message(self, message: HumanMessage) -> None:
        """
        将人类对话历史添加到消息列表中。
        """
        self.message_list.append(message)

    def add_ai_message(self, message: AIMessage) -> None:
        """
        将人类对话历史添加到消息列表中。
        """
        self.message_list.append(message)

    def modify_system_prompt(self, new_prompt: SystemMessage) -> None:
        """
        修改系统提示词。
        :param new_prompt: 新的系统提示词
        """
        self.system_prompt = new_prompt

    def to_message_list(self) -> list:
        """
        将对话历史转换为消息列表，包含系统提示词。
        :return: 消息列表
        """
        messages = [self.system_prompt] if self.system_prompt else []
        messages.extend(self.message_history)
        return messages


# 对话模型的使用示例
llm = ChatOpenAI(
api_key="sk-xxxxxxxxx",
base_url="https://api.openai-proxy.org/v1",
model="gpt-3.5-turbo",
)
response = llm.invoke("解释神经网络原理")
print(response.content)

# 类型消息示例
system_message = SystemMessage(content="你是一个专业的数据科学家")
human_message = HumanMessage(content="解释一下随机森林算法")
ai_message = AIMessage(content="随机森林是一种集成学习方法...")
custom_message = ChatMessage(role="analyst", content="补充一点关于超参数调优的信息")
messages = [system_message,human_message,ai_message, custom_message]
llm.invoke(messages)

#流式输出示例
streaming_llm = ChatOpenAI(
    api_key="sk-xxxxxxxxx",
    base_url="https://api.openai-proxy.org/v1",
    model="gpt-3.5-turbo",
    streaming=True,  # 启用流式输出
)
print("开始流式输出：")
for chunk in streaming_llm.stream(messages):
    print(chunk.content, end="", flush=True) # 刷新缓冲区 (无换行符，缓冲区未刷新，内容可能不会立即显示)
print("\n流式输出结束")

#异步调用示例
chat_model = ChatOpenAI(model="gpt-4o-mini")
async def async_test():
    messages1 = [SystemMessage(content="你是一位乐于助人的智能小助手"),
    HumanMessage(content="请帮我介绍一下什么是机器学习"), ]
    response = await chat_model.ainvoke(messages1)
    return response
async def run_concurrent_tests():
    tasks = [async_test() for _ in range(3)]
    return await asyncio.gather(*tasks)
results = asyncio.run(async_test())


#提示词示例
#普通模板
template = PromptTemplate(
template="{foo}{bar}",
input_variables=["foo","bar"],
partial_variables={"foo": "hello"} # 默认值
)
prompt = template.format(bar="world")
response = llm.invoke(prompt)

#角色对话模板
prompt_template = ChatPromptTemplate([
    # 字符串 role + 字符串 content
    ("system", "你是一个AI开发工程师. 你的名字是 {name}."),
    ("human", "你能开发哪些AI应用?"),
    ("ai", "我能开发很多AI应用, 比如聊天机器人, 图像识别, 自然语言处理等."),
    ("human", "{user_input}")
])

template = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template("你是{product}的客服助手。你的名字叫{name}"),
    HumanMessagePromptTemplate.from_template("hello 你好吗？"),
    AIMessagePromptTemplate.from_template("我很好 谢谢!"),
    MessagesPlaceholder(variable_name="history"), # 占位符
    HumanMessagePromptTemplate.from_template("{query}"),
])
prompt = template.format_messages(product="AGI课堂",name="Bob",query="你是谁",history=[HumanMessage(content="你是谁"),AIMessage(content="我是Bob")])
response = llm.invoke(prompt)

# Few-shot 模板
examples = [
    {"input": "北京天气怎么样", "output": "北京市"},
    {"input": "南京下雨吗", "output": "南京市"},
    {"input": "武汉热吗", "output": "武汉市"}
]
example_prompt = PromptTemplate.from_template(
template="Input: {input}\nOutput: {output}"
)
prompt = FewShotPromptTemplate(
examples=examples,
example_prompt=example_prompt,
suffix="Input: {input}\nOutput:",
input_variables=["input"]
)
prompt = prompt.invoke({"input":"长沙多少度"})

# Few-shot 角色对话模板
examples = [
{"input": "1+1等于几？", "output": "1+1等于2"},
{"input": "法国的首都是？", "output": "巴黎"}
]
msg_example_prompt = ChatPromptTemplate.from_messages([
("human", "{input}"),
("ai", "{output}"),
])
few_shot_prompt = FewShotChatMessagePromptTemplate(example_prompt=msg_example_prompt,examples=examples)
final_prompt = ChatPromptTemplate.from_messages([
    ('system', 'You are a helpful AI Assistant'),
    few_shot_prompt,
    ('human', '{input}'),
])

# 输出解析器
joke_query = "告诉我一个笑话。"
parser = JsonOutputParser()
prompt = PromptTemplate(template="回答用户的查询.\n{format_instructions}\n{query}\n",input_variables=["query"],partial_variables={"format_instructions": parser.get_format_instructions()},
)
chain = prompt | chat_model | parser
output = chain.invoke({"query": "给我讲一个笑话"})