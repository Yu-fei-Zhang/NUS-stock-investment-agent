# import warnings
# from abc import ABC
# from typing import Optional, Any
#
# from langchain.memory.chat_memory import BaseChatMemory
# from langchain.memory.utils import get_prompt_input_key
# from langchain_community.chat_message_histories import RedisChatMessageHistory
# from langchain_core.memory import BaseMemory
# from langchain_core.messages import HumanMessage, AIMessage, get_buffer_string, BaseMessage
#
#
# class RedisBaseChatMemory(BaseMemory, ABC):
#     """Abstract base class for redis chat memory.
#     """
#
#     chat_memory: RedisChatMessageHistory
#     output_key: Optional[str] = None
#     input_key: Optional[str] = None
#     return_messages: bool = False
#
#
#     def _get_input_output(
#         self,
#         inputs: dict[str, Any],
#         outputs: dict[str, str],
#     ) -> tuple[str, str]:
#         if self.input_key is None:
#             prompt_input_key = get_prompt_input_key(inputs, self.memory_variables)
#         else:
#             prompt_input_key = self.input_key
#         if self.output_key is None:
#             if len(outputs) == 1:
#                 output_key = next(iter(outputs.keys()))
#             elif "output" in outputs:
#                 output_key = "output"
#                 warnings.warn(
#                     f"'{self.__class__.__name__}' got multiple output keys:"
#                     f" {outputs.keys()}. The default 'output' key is being used."
#                     f" If this is not desired, please manually set 'output_key'.",
#                     stacklevel=3,
#                 )
#             else:
#                 msg = (
#                     f"Got multiple output keys: {outputs.keys()}, cannot "
#                     f"determine which to store in memory. Please set the "
#                     f"'output_key' explicitly."
#                 )
#                 raise ValueError(msg)
#         else:
#             output_key = self.output_key
#         return inputs[prompt_input_key], outputs[output_key]
#
#     def save_context(self, inputs: dict[str, Any], outputs: dict[str, str]) -> None:
#         """Save context from this conversation to buffer."""
#         input_str, output_str = self._get_input_output(inputs, outputs)
#         self.chat_memory.add_messages(
#             [
#                 HumanMessage(content=input_str),
#                 AIMessage(content=output_str),
#             ],
#         )
#
#     async def asave_context(
#         self,
#         inputs: dict[str, Any],
#         outputs: dict[str, str],
#     ) -> None:
#         """Save context from this conversation to buffer."""
#         input_str, output_str = self._get_input_output(inputs, outputs)
#         await self.chat_memory.aadd_messages(
#             [
#                 HumanMessage(content=input_str),
#                 AIMessage(content=output_str),
#             ],
#         )
#
#     def clear(self) -> None:
#         """Clear memory contents."""
#         self.chat_memory.clear()
#
#     async def aclear(self) -> None:
#         """Clear memory contents."""
#         await self.chat_memory.aclear()
#
#
# class RedisChatMemory(RedisBaseChatMemory):
#     """
#     """
#
#     human_prefix: str = "Human"
#     ai_prefix: str = "AI"
#     memory_key: str = "history"  #: :meta private:
#
#     @property
#     def buffer(self) -> Any:
#         """String buffer of memory."""
#         return self.buffer_as_messages if self.return_messages else self.buffer_as_str
#
#     async def abuffer(self) -> Any:
#         """String buffer of memory."""
#         return (
#             await self.abuffer_as_messages()
#             if self.return_messages
#             else await self.abuffer_as_str()
#         )
#
#     def _buffer_as_str(self, messages: list[BaseMessage]) -> str:
#         return get_buffer_string(
#             messages,
#             human_prefix=self.human_prefix,
#             ai_prefix=self.ai_prefix,
#         )
#
#     @property
#     def buffer_as_str(self) -> str:
#         """Exposes the buffer as a string in case return_messages is True."""
#         return self._buffer_as_str(self.chat_memory.messages)
#
#     async def abuffer_as_str(self) -> str:
#         """Exposes the buffer as a string in case return_messages is True."""
#         messages = await self.chat_memory.aget_messages()
#         return self._buffer_as_str(messages)
#
#     @property
#     def buffer_as_messages(self) -> list[BaseMessage]:
#         """Exposes the buffer as a list of messages in case return_messages is False."""
#         return self.chat_memory.messages
#
#     async def abuffer_as_messages(self) -> list[BaseMessage]:
#         """Exposes the buffer as a list of messages in case return_messages is False."""
#         return await self.chat_memory.aget_messages()
#
#     @property
#     def memory_variables(self) -> list[str]:
#         """Will always return list of memory variables.
#
#         :meta private:
#         """
#         return [self.memory_key]
#
#     def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, Any]:
#         """Return history buffer."""
#         return {self.memory_key: self.buffer}
#
#     async def aload_memory_variables(self, inputs: dict[str, Any]) -> dict[str, Any]:
#         """Return key-value pairs given the text input to the chain."""
#         buffer = await self.abuffer()
#         return {self.memory_key: buffer}


import json
import time
import redis  # 同步
from redis import asyncio as aioredis   # 异步
import warnings
from abc import ABC
from typing import Optional, Any

from langchain.memory.utils import get_prompt_input_key
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.memory import BaseMemory
from langchain_core.messages import HumanMessage, AIMessage, get_buffer_string, BaseMessage


class RedisBaseChatMemory(BaseMemory, ABC):
    """Abstract base class for **Redis-backed** chat memory."""
    chat_memory: RedisChatMessageHistory
    output_key: Optional[str] = None
    input_key: Optional[str] = None
    return_messages: bool = False
    redis_url: str = "redis://localhost:6379/0"
    # ========== 1. 字段优先级适配常见 Redis 场景 ==========
    _INPUT_CANDIDATES = ("prompt", "query", "input")
    _OUTPUT_CANDIDATES = ("answer", "response", "output")

    def _get_input_output(
        self,
        inputs: dict[str, Any],
        outputs: dict[str, str],
    ) -> tuple[str, str]:
        """按候选键优先级抽取输入/输出文本，适配 Redis 记忆存储。"""
        if self.input_key is None:
            prompt_input_key = next((k for k in self._INPUT_CANDIDATES if k in inputs), None)
            if prompt_input_key is None:
                raise KeyError(
                    f"Cannot find any of {self._INPUT_CANDIDATES} in inputs keys: {list(inputs.keys())}"
                )
        else:
            prompt_input_key = self.input_key

        if self.output_key is None:
            output_key = next((k for k in self._OUTPUT_CANDIDATES if k in outputs), None)
            if output_key is None:
                raise KeyError(
                    f"Cannot find any of {self._OUTPUT_CANDIDATES} in outputs keys: {list(outputs.keys())}"
                )
        else:
            output_key = self.output_key

        return inputs[prompt_input_key], outputs[output_key]

    # ========== 2. 双写：消息列表 + 原始文本 Hash ==========
    def save_context(self, inputs: dict[str, Any], outputs: dict[str, str]) -> None:
        input_str, output_str = self._get_input_output(inputs, outputs)

        # ① 正常写消息列表
        self.chat_memory.add_messages(
            [HumanMessage(content=input_str), AIMessage(content=output_str)]
        )

        # ② 独立客户端 → 用自己的 redis_url
        rc = redis.from_url(self.redis_url, decode_responses=True)
        session_id = self.chat_memory.session_id
        key = f"chat:raw:{session_id}"
        field = str(int(time.time() * 1000))
        value = json.dumps({"human": input_str, "ai": output_str}, ensure_ascii=False)
        rc.hset(key, field, value)

    async def asave_context(self, inputs: dict[str, Any], outputs: dict[str, str]) -> None:
        input_str, output_str = self._get_input_output(inputs, outputs)
        await self.chat_memory.aadd_messages(
            [HumanMessage(content=input_str), AIMessage(content=output_str)]
        )

        rc = aioredis.from_url(self.redis_url, decode_responses=True)
        session_id = self.chat_memory.session_id
        key = f"chat:raw:{session_id}"
        field = str(int(time.time() * 1000))
        value = json.dumps({"human": input_str, "ai": output_str}, ensure_ascii=False)
        await rc.hset(key, field, value)

    def clear(self) -> None:
        self.chat_memory.clear()

    async def aclear(self) -> None:
        await self.chat_memory.aclear()


class RedisChatMemory(RedisBaseChatMemory):
    human_prefix: str = "Human"
    ai_prefix: str = "AI"
    memory_key: str = "history"

    @property
    def buffer(self) -> Any:
        return self.buffer_as_messages if self.return_messages else self.buffer_as_str

    async def abuffer(self) -> Any:
        return (
            await self.abuffer_as_messages()
            if self.return_messages
            else await self.abuffer_as_str()
        )

    def _buffer_as_str(self, messages: list[BaseMessage]) -> str:
        return get_buffer_string(
            messages,
            human_prefix=self.human_prefix,
            ai_prefix=self.ai_prefix,
        )

    @property
    def buffer_as_str(self) -> str:
        return self._buffer_as_str(self.chat_memory.messages)

    async def abuffer_as_str(self) -> str:
        messages = await self.chat_memory.aget_messages()
        return self._buffer_as_str(messages)

    @property
    def buffer_as_messages(self) -> list[BaseMessage]:
        return self.chat_memory.messages

    async def abuffer_as_messages(self) -> list[BaseMessage]:
        return await self.chat_memory.aget_messages()

    @property
    def memory_variables(self) -> list[str]:
        return [self.memory_key]

    def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, Any]:
        return {self.memory_key: self.buffer}

    async def aload_memory_variables(self, inputs: dict[str, Any]) -> dict[str, Any]:
        buffer = await self.abuffer()
        return {self.memory_key: buffer}