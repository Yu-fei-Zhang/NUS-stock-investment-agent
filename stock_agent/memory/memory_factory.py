# memory_factory.py
from langchain_community.chat_message_histories import RedisChatMessageHistory
from Short_termMemory import RedisChatMemory


def create_redis_memory(session_id: str, redis_url: str = "redis://localhost:6379/0"):
    """创建 Redis 聊天记忆实例"""
    chat_memory = RedisChatMessageHistory(
        session_id=session_id,
        url=redis_url,
        key_prefix="chat_history:",
        ttl=3600
    )

    memory = RedisChatMemory(
        chat_memory=chat_memory,
        return_messages=False,
        human_prefix="Human",
        ai_prefix="AI",
        memory_key="history"
    )

    return memory