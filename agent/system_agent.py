# 导入日志工具
from utils.Logger import Logger
# 导入LangGraph预建智能体
from langgraph.prebuilt import create_react_agent
# 导入自定义模型类
from model.model import MyModel
# 导入邮件发送工具
from tool.send_email_tool import send_email
# 导入MySQL查询工具
from tool.mysql_tool import mysql_tool

# 获取日志记录器实例
logger = Logger.get_logger()

"""
【修改】登陆验证码智能体
功能：验证用户邮箱是否存在，并发送4位验证码邮件
工作流程：
  1. 查询MySQL数据库users表验证邮箱是否注册
  2. 如果邮箱存在，生成4位随机验证码并发送邮件
  3. 返回JSON格式的结果（包含状态码、提示信息和验证码）
"""


class SystemAgent:
    # 初始化方法：创建模型、工具和智能体实例
    def __init__(self):
        logger.info("初始化登陆验证码智能体")

        # 获取LLM模型实例（单例模式）
        self.model = MyModel.get_line_model()
        # 初始化工具列表
        self.tools = self.init_tools()
        # 创建智能体
        self.agent = self.init_agent()

    # 初始化工具列表：包含MySQL查询和邮件发送两个工具
    def init_tools(self):
        # mysql_tool: 用于查询users表验证邮箱是否存在
        # send_email_tool: 用于发送验证码邮件
        self.tools = [mysql_tool, send_email]
        return self.tools

    # 初始化智能体：配置系统提示词和创建agent实例
    def init_agent(self):
        prompt = """你是一个登录验证助手，你有两个工具：mysql_tool（执行SQL查询）和 send_email（发送邮件）。

工作流程：
1. 根据用户输入的邮箱，调用 mysql_tool 查询 users 表确认邮箱是否存在
   SQL示例：SELECT * FROM users WHERE email = '用户输入的邮箱'
2. 如果邮箱存在，生成4位随机数字验证码，调用 send_email 发送邮件
   - to: 查询到的用户邮箱
   - subject: "登录验证码"
   - content: "您的验证码是：XXXX（4位数字），有效期5分钟。"

输出格式（严格遵守，只输出JSON，不要任何其他文字，不要用markdown代码块包裹）：
- 邮箱不存在：{"code": "500", "msg": "邮箱未注册", "data": ""}
- 发送成功：{"code": "200", "msg": "发送成功", "data": "1234"}
- 发送失败：{"code": "500", "msg": "失败原因", "data": ""}
"""
        self.agent = create_react_agent(model=self.model, prompt=prompt, tools=self.tools)
        return self.agent

    # 处理用户问题：验证邮箱并发送验证码
    # 参数 question: 用户输入的问题，例如"用户的邮箱是 3082686649@qq.com"
    # 返回: JSON格式的字符串，包含code、msg和data字段
    def answer(self, question):
        # 调用智能体处理用户问题
        rs = self.agent.invoke({"messages": [{"role": "user", "content": question}]})
        # 获取最后一条消息内容（智能体返回的JSON字符串）
        answer_content = rs["messages"][-1].content
        # 记录日志
        logger.info(f"智能体返回结果：{answer_content}")
        return answer_content


if __name__ == "__main__":
    agent = SystemAgent()
    agent.answer("用户的邮箱是 3493985772@qq.com")
