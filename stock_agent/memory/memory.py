# memory.py - Short-term Memory 完整实现
from abc import ABC, abstractmethod
from typing import Optional

from langchain.chains.llm import LLMChain
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import OpenAI, ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import CharacterTextSplitter

from memory_factory import create_redis_memory


# ============================================================================
# Short-term Memory 实现
# ============================================================================

class ShortTermMemoryDemo:
    """Short-term Memory 演示类"""

    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0):
        """初始化

        Args:
            model: 使用的模型名称
            temperature: 温度参数，控制输出的随机性
        """
        self.model = model
        self.temperature = temperature
        self.llm = OpenAI(model=model, temperature=temperature)
        self.chat_llm = ChatOpenAI(model=model, temperature=temperature)

    # ========================================================================
    # 1. ConversationBufferMemory - 基础对话缓冲记忆
    # ========================================================================

    def demo_buffer_memory_basic(self):
        """演示基础的 ConversationBufferMemory"""
        print("\n" + "=" * 70)
        print("1. ConversationBufferMemory - 基础对话缓冲记忆")
        print("=" * 70)

        # 创建提示模板
        template = """你可以与人类对话。
当前对话: {history}
人类问题: {question}
回复:"""

        prompt = PromptTemplate.from_template(template)
        memory = ConversationBufferMemory()
        chain = LLMChain(llm=self.llm, prompt=prompt, memory=memory)

        # 第一轮对话
        print("\n第一轮对话:")
        result1 = chain.invoke({"question": "我的名字叫Tom"})
        print(f"问题: 我的名字叫Tom")
        print(f"回答: {result1['text']}")

        # 第二轮对话（测试记忆）
        print("\n第二轮对话:")
        result2 = chain.invoke({"question": "我叫什么名字？"})
        print(f"问题: 我叫什么名字？")
        print(f"回答: {result2['text']}")

        # 查看记忆内容
        print("\n记忆内容:")
        print(memory.load_memory_variables({}))

        print("\n✅ ConversationBufferMemory 基础演示完成")
        return memory

    def demo_buffer_memory_with_messages(self):
        """演示使用消息格式的 ConversationBufferMemory"""
        print("\n" + "=" * 70)
        print("2. ConversationBufferMemory - 消息格式（return_messages=True）")
        print("=" * 70)

        # 创建聊天提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个与人类对话的机器人。"),
            MessagesPlaceholder(variable_name='history'),
            ("human", "问题：{question}")
        ])

        # return_messages=True 会返回消息对象列表而非字符串
        memory = ConversationBufferMemory(return_messages=True)
        chain = LLMChain(prompt=prompt, llm=self.chat_llm, memory=memory)

        # 对话示例
        print("\n对话 1:")
        result1 = chain.invoke({"question": "中国首都在哪里？"})
        print(f"问题: 中国首都在哪里？")
        print(f"回答: {result1['text']}")

        print("\n对话 2:")
        result2 = chain.invoke({"question": "那里有什么著名景点？"})
        print(f"问题: 那里有什么著名景点？")
        print(f"回答: {result2['text']}")

        # 查看消息格式的记忆
        print("\n记忆内容（消息格式）:")
        memory_vars = memory.load_memory_variables({})
        for msg in memory_vars['history']:
            print(f"  {msg.type}: {msg.content}")

        print("\n✅ ConversationBufferMemory 消息格式演示完成")
        return memory

    # ========================================================================
    # 2. ConversationBufferWindowMemory - 窗口记忆
    # ========================================================================

    def demo_window_memory(self, k: int = 2):
        """演示 ConversationBufferWindowMemory

        Args:
            k: 保留最近 k 轮对话
        """
        print("\n" + "=" * 70)
        print(f"3. ConversationBufferWindowMemory - 窗口记忆（k={k}）")
        print("=" * 70)

        memory = ConversationBufferWindowMemory(k=k)

        # 保存多轮对话
        print("\n保存对话:")
        conversations = [
            ({"input": "你好"}, {"output": "怎么了"}),
            ({"input": "你是谁"}, {"output": "我是AI助手"}),
            ({"input": "你的生日是哪天？"}, {"output": "我不清楚"}),
        ]

        for i, (input_msg, output_msg) in enumerate(conversations, 1):
            memory.save_context(input_msg, output_msg)
            print(f"  对话 {i}: {input_msg['input']} -> {output_msg['output']}")

        # 查看记忆（只保留最近 k 轮）
        print(f"\n记忆内容（只保留最近 {k} 轮）:")
        history = memory.load_memory_variables({})
        print(history['history'])

        print(f"\n✅ ConversationBufferWindowMemory 演示完成")
        return memory

    # ========================================================================
    # 3. Redis Memory - 持久化记忆
    # ========================================================================

    def demo_redis_memory(self, session_id: str = "demo_user_001"):
        """演示 Redis 持久化记忆

        Args:
            session_id: 会话ID，用于区分不同用户
        """
        print("\n" + "=" * 70)
        print("4. Redis Memory - 持久化记忆")
        print("=" * 70)

        # 创建 Redis 记忆
        memory = create_redis_memory(session_id=session_id)
        print(f"✅ 已为会话 '{session_id}' 创建 Redis 记忆")

        # 保存对话
        print("\n保存对话到 Redis:")
        conversations = [
            ("我叫张三", "你好张三！很高兴认识你。"),
            ("我喜欢编程", "编程是个很好的爱好！"),
            ("我在学习 Python", "Python 是一门很强大的语言。"),
        ]

        for i, (user_msg, ai_msg) in enumerate(conversations, 1):
            memory.save_context(
                inputs={"input": user_msg},
                outputs={"output": ai_msg}
            )
            print(f"  对话 {i}: {user_msg} -> {ai_msg}")

        # 读取记忆
        print("\n从 Redis 读取记忆:")
        history = memory.load_memory_variables({})
        print(history['history'])

        # 验证持久化
        print("\n验证持久化（重新创建实例）:")
        memory2 = create_redis_memory(session_id=session_id)
        history2 = memory2.load_memory_variables({})

        if history2["history"] == history["history"]:
            print("✅ 持久化验证成功！数据已正确保存到 Redis")
        else:
            print("⚠️ 持久化验证失败")

        # 清理（可选）
        print("\n清理测试数据...")
        memory.clear()
        print("✅ Redis Memory 演示完成")

        return memory

    # ========================================================================
    # 4. LLM + Redis Memory 完整集成
    # ========================================================================

    def demo_llm_with_redis_memory(self, session_id: str = "llm_demo_user"):
        """演示 LLM 与 Redis Memory 完整集成

        Args:
            session_id: 会话ID
        """
        print("\n" + "=" * 70)
        print("5. LLM + Redis Memory 完整集成")
        print("=" * 70)

        # 创建 Redis 记忆
        memory = create_redis_memory(session_id=session_id)
        print(f"✅ 已为会话 '{session_id}' 创建记忆")

        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个友好的AI助手，你会记住用户告诉你的信息。"),
            MessagesPlaceholder(variable_name='history'),
            ("human", "{question}")
        ])

        # 创建链
        chain = LLMChain(prompt=prompt, llm=self.chat_llm, memory=memory)

        # 多轮对话
        questions = [
            "我叫李雷，今年25岁",
            "我喜欢打篮球",
            "你还记得我的名字和年龄吗？我的爱好是什么？"
        ]

        print("\n开始多轮对话:")
        for i, question in enumerate(questions, 1):
            print(f"\n--- 对话 {i} ---")
            print(f"用户: {question}")
            result = chain.invoke({"question": question})
            print(f"AI: {result['text']}")

        # 显示完整历史
        print("\n完整对话历史（存储在 Redis 中）:")
        print("-" * 70)
        history = memory.load_memory_variables({})
        print(history['history'])
        print("-" * 70)

        # 清理
        print("\n清理测试数据...")
        memory.clear()
        print("✅ LLM + Redis Memory 集成演示完成")

        return memory

    # ========================================================================
    # 5. RAG（检索增强生成）
    # ========================================================================

    def demo_rag(self, file_path: str = "./asset/load/10-test_doc.txt"):
        """演示 RAG 系统

        Args:
            file_path: 文档文件路径
        """
        print("\n" + "=" * 70)
        print("6. RAG - 检索增强生成")
        print("=" * 70)

        try:
            # 1. 创建提示模板
            prompt_template = """请使用以下提供的文本内容来回答问题。
仅使用提供的文本信息，如果文本中没有相关信息，请回答"抱歉，提供的文本中没有这个信息"。

文本内容：
{context}

问题：{question}

回答：
"""
            prompt = PromptTemplate.from_template(prompt_template)

            # 2. 创建 LLM 和嵌入模型
            llm = ChatOpenAI(model=self.model, temperature=0)
            embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")

            print(f"\n加载文档: {file_path}")
            # 3. 加载文档
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
            print(f"✅ 成功加载 {len(documents)} 个文档")

            # 4. 分割文档
            print("\n分割文档...")
            text_splitter = CharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100,
            )
            texts = text_splitter.split_documents(documents)
            print(f"✅ 文档分割为 {len(texts)} 个片段")

            # 5. 创建向量存储
            print("\n创建向量存储...")
            vectorstore = FAISS.from_documents(
                documents=texts,
                embedding=embedding_model
            )
            retriever = vectorstore.as_retriever()
            print("✅ 向量存储创建完成")

            # 6. 检索和回答
            question = "北京有什么著名的建筑？"
            print(f"\n问题: {question}")

            print("检索相关文档...")
            docs = retriever.invoke(question)
            print(f"✅ 找到 {len(docs)} 个相关文档片段")

            # 7. 生成回答
            print("\n生成回答...")
            chain = prompt | llm
            result = chain.invoke(input={
                "question": question,
                "context": docs
            })

            print("\n" + "=" * 70)
            print(f"回答: {result.content}")
            print("=" * 70)

            print("\n✅ RAG 演示完成")
            return result

        except FileNotFoundError:
            print(f"\n❌ 错误: 找不到文件 '{file_path}'")
            print("请确保文件存在或修改 file_path 参数")
            return None
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            return None

    # ========================================================================
    # 运行所有演示
    # ========================================================================

    def run_all_demos(self):
        """运行所有演示"""
        print("\n" + "=" * 70)
        print("Short-term Memory 完整演示")
        print("=" * 70)

        try:
            # 1. 基础内存缓冲
            self.demo_buffer_memory_basic()
            input("\n按 Enter 继续下一个演示...")

            # 2. 消息格式的内存缓冲
            self.demo_buffer_memory_with_messages()
            input("\n按 Enter 继续下一个演示...")

            # 3. 窗口记忆
            self.demo_window_memory(k=2)
            input("\n按 Enter 继续下一个演示...")

            # 4. Redis 持久化记忆
            self.demo_redis_memory()
            input("\n按 Enter 继续下一个演示...")

            # 5. LLM + Redis Memory 集成
            self.demo_llm_with_redis_memory()
            input("\n按 Enter 继续下一个演示...")

            # 6. RAG
            self.demo_rag()

            print("\n" + "=" * 70)
            print("🎉 所有演示完成！")
            print("=" * 70)

        except KeyboardInterrupt:
            print("\n\n用户中断演示")
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("Short-term Memory 演示系统")
    print("=" * 70)
    print("\n选择要运行的演示：")
    print("1. ConversationBufferMemory - 基础")
    print("2. ConversationBufferMemory - 消息格式")
    print("3. ConversationBufferWindowMemory - 窗口记忆")
    print("4. Redis Memory - 持久化记忆")
    print("5. LLM + Redis Memory - 完整集成")
    print("6. RAG - 检索增强生成")
    print("7. 运行所有演示")
    print("0. 退出")

    demo = ShortTermMemoryDemo()

    while True:
        try:
            choice = input("\n请输入选项 (0-7): ").strip()

            if choice == "0":
                print("\n再见！")
                break
            elif choice == "1":
                demo.demo_buffer_memory_basic()
            elif choice == "2":
                demo.demo_buffer_memory_with_messages()
            elif choice == "3":
                demo.demo_window_memory()
            elif choice == "4":
                demo.demo_redis_memory()
            elif choice == "5":
                demo.demo_llm_with_redis_memory()
            elif choice == "6":
                demo.demo_rag()
            elif choice == "7":
                demo.run_all_demos()
                break
            else:
                print("❌ 无效选项，请重新输入")

        except KeyboardInterrupt:
            print("\n\n用户中断")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()