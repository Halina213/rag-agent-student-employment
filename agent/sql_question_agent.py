from utils.Logger import Logger
from langgraph.prebuilt import create_react_agent
from model.model import MyModel
from tool.mysql_tool import mysql_tool
from langgraph.checkpoint.memory import MemorySaver
import asyncio

logger = Logger.get_logger(__name__)

"""
sql问答智能体
【修改】更新提示词中的数据库表结构说明为 PSEO 就业与收入数据
【修改】使用 create_react_agent 替代 create_agent
【修改】使用 MemorySaver 替代 InMemorySaver
"""


# 【修改】新的数据库表结构说明 - PSEO就业与收入数据
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


class SqlQuestionAgent:
    # 初始化
    def __init__(self):
        logger.info("初始化sql问答助手智能体")
        self.model = MyModel.get_line_model()
        self.tools = self.init_tools()
        self.agent = self.init_agent()

    # 初始化工具
    def init_tools(self):
        self.tools = [mysql_tool]
        return self.tools

    # 创建智能体
    def init_agent(self):
        # 【修改】更新提示词，包含新的数据库表结构说明
        prompt = f"""
【重要】你是一个 PSEO 高校毕业生就业与收入数据分析系统的SQL问答助手。

一：你有一个工具 mysql_tool 执行SQL查询

{DATABASE_SCHEMA}

二：重要规则
1. **SQL生成规范**:
   - 只能使用SELECT查询，禁止使用INSERT/UPDATE/DELETE等修改操作
   - 只查询student_placement表
2. **查询原则**:
   - 涉及排名或TOP N时，必须使用ORDER BY和LIMIT
   - 只查询前10条记录
   - 就业率优先使用 employment_rate；为空时可用 employment_count*100.0/NULLIF(total_graduates,0) 计算
   - 收入分析优先使用 median_earnings_1yr、median_earnings_5yr、median_earnings_10yr
"""
        # 使用 MemorySaver 替代 InMemorySaver
        memory = MemorySaver()
        # 使用 create_react_agent 替代 create_agent
        # 使用 messages_modifier 替代 system_prompt
        self.agent = create_react_agent(
            model=self.model,
            prompt=prompt,
            tools=self.tools,
            checkpointer=memory
        )
        return self.agent

    # 运行智能体() - 异步
    async def answer(self, question, user_id):
        rs = self.agent.astream(
            {"messages": [{"role": "user", "content": question}]},
            {"configurable": {"thread_id": user_id}},
            stream_mode="messages"  # 支持流式输出
        )
        # 遍历流式响应
        async for c, m in rs:
            # 判断是否是工具调用，不返回工具调用的结果
            if not hasattr(c, "tool_call_id"):
                yield c.content  # 逐步返回AI的回答


if __name__ == "__main__":
    agent = SqlQuestionAgent()

    # 定义一个处理异步的迭代器
    async def gernert():
        async for x in agent.answer("收入最高的10个专业是什么", 10):
            print(x, end="")

    # 运行迭代器
    asyncio.run(gernert())
