import json
from langchain_core.messages import SystemMessage, HumanMessage
from model.model import MyModel
from utils.Logger import Logger

logger = Logger.get_logger(__name__)

INTENTS = {"chart", "analysis", "query"}

_SYS_PROMPT = """你是一个用户意图分类器，只做分类，不做别的。
根据用户问题判断它属于哪一类：
- chart：想画图/可视化（柱状图、折线图、饼图、散点图、雷达图、画个图、可视化）
- analysis：想要分析/统计/报告/总结/趋势/对比结论
- query：普通数据查询（问一个事实、明细、排名、具体数值）

只输出一个 JSON，格式：{"intent": "chart|analysis|query", "reason": "一句话原因"}
不要输出任何其他文字，不要用 markdown 代码块包裹。"""


def classify_intent(question: str) -> str:
    """用大模型判断用户意图，返回 chart / analysis / query。失败时回退 query。"""
    try:
        model = MyModel.get_model()
        resp = model.invoke([
            SystemMessage(content=_SYS_PROMPT),
            HumanMessage(content=question),
        ])
        text = (resp.content or "").strip()
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            obj = json.loads(text[start:end + 1])
            intent = obj.get("intent")
            if intent in INTENTS:
                logger.info(f"意图路由：{intent}（{obj.get('reason', '')}）")
                return intent
    except Exception as e:
        logger.warning(f"意图分类失败，回退 query：{e}")
    return "query"