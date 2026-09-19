from langgraph.prebuilt import create_react_agent
from utils.Logger import Logger
from langchain_core.messages import HumanMessage
from model.model import MyModel
from tool.mysql_tool import mysql_tool
from langgraph.checkpoint.memory import MemorySaver
import json
import os
from dotenv import load_dotenv

load_dotenv()
logger = Logger.get_logger(__name__)

DATABASE_SCHEMA = """
【重要】数据库表结构说明 - PSEO 高校毕业生就业与收入数据分析系统

## student_placement PSEO就业与收入数据表
字段说明：
- institution_id(学校/机构ID) - VARCHAR
- institution_name(学校/机构名称) - VARCHAR
- institution_state(学校所在州/地区) - VARCHAR
- institution_type(学校类型或层级) - VARCHAR
- degree_level(学历层级) - VARCHAR
- degree_field(专业/学科字段) - VARCHAR
- major_category(专业大类) - VARCHAR
- graduation_year(毕业年份) - INT
- cohort_year(毕业 cohort/统计批次) - VARCHAR
- industry(就业行业) - VARCHAR
- employment_count(就业人数) - INT
- total_graduates(毕业生人数/样本人数) - INT
- employment_rate(就业率) - DOUBLE，已按0-100百分比保存
- median_earnings_1yr(毕业后1年收入中位数) - DOUBLE
- median_earnings_5yr(毕业后5年收入中位数) - DOUBLE
- median_earnings_10yr(毕业后10年收入中位数) - DOUBLE
- p25_earnings(收入第25百分位) - DOUBLE
- p75_earnings(收入第75百分位) - DOUBLE
"""


class EchartsAgent:
    def __init__(self):
        logger.info("初始化Echarts图表智能体")
        self.model = MyModel().get_line_model()
        self.model.model_kwargs = {"tool_choice": "auto"}
        self.tools = [mysql_tool]
        self.checkpointer = MemorySaver()

    def answer(self, question: str, user_id: str):
        prompt = """你是「小智」的图表分身 📊✨，专门帮用户把数据变成漂亮的图表！
你有工具 mysql_tool 执行SQL查询。

""" + DATABASE_SCHEMA + """

个性化能力：
- 如果用户信息中包含姓名和学院，在图表标题中可以体现用户关注的方向
- 如果用户来自某个学院，优先展示与该学院相关的数据对比
- 根据用户要求的详细程度调整图表复杂度
- 图表标题要有温度，比如"小雨关注的专业收入洞察📊"而不是冷冰冰的"收入统计"

工作流程：
1. 根据用户问题，调用 mysql_tool 查询 student_placement 表获取数据
2. 用查询结果生成 ECharts 图表配置

图表生成规范：
- 图表必须有标题(title.text)，标题要有亲和力
- 图表必须有工具栏(toolbox.feature.saveAsImage)
- 涉及排名时使用 ORDER BY 和 LIMIT，最多展示10条
- 只能使用SELECT查询
- 【关键】就业率优先使用 employment_rate 字段；如果该字段为空且有就业人数和毕业生人数，可用 employment_count*100.0/NULLIF(total_graduates,0) AS employment_rate 计算
- 收入图表优先使用 median_earnings_1yr、median_earnings_5yr、median_earnings_10yr
- 常用分组维度：institution_name、institution_state、degree_level、degree_field、major_category、industry、graduation_year
- 图表中所有涉及百分比的数据，数值范围应为0-100，而非0-1
- label和tooltip中显示百分比时格式为"{c}%"

配色方案：使用温暖有活力的配色 #5470C6, #91CC75, #FAC858, #EE6666, #73C0DE

输出格式（严格遵守）：
只输出一个纯JSON格式的ECharts option对象，不要任何其他文字说明，不要用markdown代码块包裹。
直接用单花括号输出，例如：{"title":{"text":"✨ 就业率分析"},"tooltip":{"trigger":"axis"},"xAxis":{"type":"category","data":["A","B"]},"yAxis":{"type":"value"},"series":[{"type":"bar","data":[80,90]}],"toolbox":{"feature":{"saveAsImage":{}}}}

绝对不要输出 ```json ... ``` 包裹，不要在JSON前后添加任何说明文字。
"""
        msg = HumanMessage(content=question)

        try:
            agent = create_react_agent(
                model=self.model,
                prompt=prompt,
                tools=self.tools,
                checkpointer=self.checkpointer,
            )
            rs = agent.invoke({"messages": [msg]}, {"configurable": {"thread_id": user_id}})
            answer = rs["messages"][-1].content
            logger.info(f"图表智能体返回：{answer[:200]}")
            return answer
        except Exception as e:
            logger.error(f"Echarts图表生成失败：{str(e)}")
            return json.dumps({"title": {"text": "生成失败"}, "series": []})


if __name__ == "__main__":
    agent = EchartsAgent()
    print(agent.answer(
        question="用柱状图分析不同专业的毕业后1年收入中位数",
        user_id="3082686649@qq.com"
    ))
