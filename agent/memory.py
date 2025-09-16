from abc import ABC, abstractmethod

# MemoryMessage 是所有记忆消息的抽象基类。
# 其子类可用于表示存储在 MySQL、Redis、向量数据库等不同后端中的一条数据。
# 通过继承该类，可以统一管理和操作各种类型的记忆数据。
class MemoryMessage(ABC):
    pass

# MemoryManager 是记忆管理的抽象基类，定义了通用的记忆操作接口。
# 子类可实现具体的存储和检索逻辑，支持多种后端（如数据库、缓存、向量存储等）。
class MemoryManager(ABC):
    @abstractmethod
    def get_memory_by_key(self, key: str) -> MemoryMessage:
        """
        抽象方法：根据 key 获取对应的 memory。
        子类需实现具体的检索逻辑。
        :param key: memory 的唯一标识
        :return: MemoryMessage 实例，代表一条记忆数据
        """
        pass

    @abstractmethod
    def get_memories_by_keys(self, key: list) -> list[MemoryMessage]:
        """
        抽象方法：根据 keys 获取对应的 memories。
        子类需实现具体的检索逻辑。
        :param key: memory 唯一标识列表
        :return: MemoryMessage 实例列表
        """
        pass

    @abstractmethod
    def put_memory_by_key(self, key: str):
        """
        抽象方法：根据 key 存储对应的 memory。
        子类需实现具体的存储逻辑。
        :param key: memory 的唯一标识
        """
        pass

    @abstractmethod
    def put_memories_by_keys(self, key: list):
        """
        抽象方法：根据 key 存储对应的 memory。
        子类需实现具体的存储逻辑。
        :param key: memory 唯一标识列表
        """
        pass
