from typing import Any, Optional
from langchain.schema import (
    SystemMessage,  # 系统消息：定义助手的角色和行为准则
    HumanMessage,   # 人类消息：用户输入的内容
    AIMessage       # AI消息：模型的回复内容
)
from abc import ABC

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