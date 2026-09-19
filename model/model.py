import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


class MyModel:
    """统一管理大模型实例。"""

    _model = None
    _line_model = None

    @staticmethod
    def _build_model(streaming: bool = False):
        model_name = os.getenv("MODEL_NAME", "qwen-plus")
        api_key = os.getenv("OPENAI_API_KEY")
        api_base = os.getenv("OPENAI_API_BASE") or os.getenv("OPENAI_BASE_URL")

        if not api_key:
            raise RuntimeError("未配置 OPENAI_API_KEY，请先复制 .env.example 为 .env 并填写模型 Key")

        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=api_base,
            streaming=streaming,
            temperature=0.2,
        )

    @staticmethod
    def get_line_model():
        if MyModel._line_model is None:
            MyModel._line_model = MyModel._build_model(streaming=True)
        return MyModel._line_model

    @staticmethod
    def get_model():
        if MyModel._model is None:
            MyModel._model = MyModel._build_model(streaming=False)
        return MyModel._model
