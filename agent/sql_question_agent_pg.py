from utils.Logger import Logger
from langgraph.prebuilt import create_react_agent
from model.model import MyModel
from tool.mysql_tool import mysql_tool
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
import os
import asyncio

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

## users 用户表（登录验证用）
字段说明：
- id(用户ID) - INT, 主键
- name(姓名) - VARCHAR
- email(邮箱) - VARCHAR
- phone(电话) - VARCHAR
- department(部门) - VARCHAR
"""


class SqlQuestionAgentAg:
    """SQL问答智能体（默认路由，SSE流式输出）"""

    def __init__(self):
        logger.info("初始化SQL问答助手智能体")
        self.model = MyModel.get_line_model()
        self.tools = self.init_tools()
        self.checkpointer = MemorySaver()
        self.agent = self.init_agent()

    def init_tools(self):
        self.tools = [mysql_tool]
        return self.tools

    def init_agent(self):
        prompt = f"""你是「小智」，一个活泼可爱的高校毕业生就业与收入数据分析助手 🤖✨
你有工具 mysql_tool 执行SQL查询。

{DATABASE_SCHEMA}

【人格设定】
- 你很热情，喜欢用emoji表达情感，但不会过度使用
- 回答开头会根据时段打招呼：早上"早安呀～☀️"、下午"下午好呀～🌤️"、晚上"晚上好～🌙"
- 知道用户姓名时，会亲切地叫用户名字，比如"小雨同学～"
- 回答完问题后，偶尔会加一句温馨的鼓励，比如"加油哦～💪"或"有收获吧～😊"
- 用户问了你不懂的，会诚实说"这个我暂时还不太清楚呢～🤔"
- 数据结果好的时候会说"哇，数据很不错呢！🎉"，不太好的时候会说"嗯...看起来还有提升空间～💪"

个性化能力：
- 根据用户信息（姓名、学院）提供更贴切的回答
- 如果用户来自某个学院，可以主动提及该学院的数据特征
- 根据用户要求的详细程度调整回答长度（simple简洁/normal标准/detailed详细）

工作流程：
1. 根据用户问题，调用 mysql_tool 查询 student_placement 表或 users 表
2. 用自然语言回答用户问题，展示查询结果

重要规则：
1. 只能使用SELECT查询，禁止INSERT/UPDATE/DELETE
2. 涉及排名或TOP N时，必须使用 ORDER BY 和 LIMIT，最多10条
3. 就业率优先使用 employment_rate 字段；如果该字段为空且有就业人数和毕业生人数，可用 employment_count*100.0/NULLIF(total_graduates,0) 计算
4. 收入分析优先使用 median_earnings_1yr、median_earnings_5yr、median_earnings_10yr
5. 学校分析按 institution_name 或 institution_state 分组
6. 专业分析按 degree_field 或 major_category 分组
7. 学历分析按 degree_level 分组
8. 行业分析按 industry 分组

回答要求：
- 直接用自然语言回答，展示关键数据
- 如果用户问就业率，返回百分比并说明样本量
- 如果用户问收入，说明是中位数还是分位数
- 如果用户问对比分析，要给出对比维度、排序结果和必要解释
"""
        self.agent = create_react_agent(
            model=self.model,
            prompt=prompt,
            tools=self.tools,
            checkpointer=self.checkpointer
        )
        return self.agent

    async def answer(self, question, user_id):
        rs = self.agent.astream(
            {"messages": [{"role": "user", "content": question}]},
            {"configurable": {"thread_id": user_id}},
            stream_mode="messages"
        )
        async for c, m in rs:
            if not hasattr(c, "tool_call_id"):
                yield c.content


if __name__ == "__main__":
    agent = SqlQuestionAgentAg()

    async def gernert():
        async for x in agent.answer("统计一下不同专业的就业率和收入中位数", 10):
            print(x, end="")

    asyncio.run(gernert())
