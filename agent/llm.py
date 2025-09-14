from langchain.llms import OpenAI

def get_llm(model_name="openai", temperature=0.2):
    if model_name == "openai":
        return OpenAI(temperature=temperature)
    else:
        raise ValueError(f"Unsupported LLM model: {model_name}")

class LLMComponent:
    def extract_profile(self, user_input):
        # 解析用户投资目标、风险偏好、财务状况
        pass

    def summarize_stock(self, stock_data):
        # 生成股票分析报告
        pass

    def generate_plan(self, profile, reports):
        # 综合用户画像和股票报告，生成投资方案
        pass
