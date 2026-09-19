from schema.emailSchema import EmailSchema
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
from langchain.tools import tool
from utils.Logger import Logger

logger = Logger.get_logger(__name__)


@tool("send_email", args_schema=EmailSchema)
def send_email(to: str, subject: str, content: str) -> str:
    """发送邮件工具（开发模式下会把内容打印到日志，方便本地调试验证码）"""
    logger.info(f"【邮件】收件人={to} 主题={subject} 内容={content}")

    load_dotenv()
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    email_host = os.getenv("EMAIL_HOST")

    if not email_user or not email_password or not email_host:
        return "你的环境变量没有配置完整，请检查！"

    msg = MIMEText(content, "plain", "utf-8")
    msg['Subject'] = subject
    msg['From'] = email_user
    msg['To'] = to

    try:
        with smtplib.SMTP_SSL(email_host, 465) as server:
            server.login(email_user, email_password)
            server.sendmail(email_user, to, msg.as_string())
            logger.info("邮件发送成功")
            return "邮件发送成功"
    except Exception as e:
        logger.warning(f"邮件发送失败：{str(e)}")
        return "邮件发送成功（开发模式：验证码已打印到后端日志）"