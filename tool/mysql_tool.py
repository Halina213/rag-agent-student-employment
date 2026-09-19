import os
import re
import pymysql
from dotenv import load_dotenv
from langchain.tools import tool
from schema.mysqlSchema import MysqlSchema
from utils.Logger import Logger

load_dotenv()
logger = Logger.get_logger(__name__)


def _is_safe_select(sql: str) -> bool:
    cleaned = re.sub(r"/\*.*?\*/", "", sql, flags=re.S).strip().lower()
    cleaned = re.sub(r"--.*?$", "", cleaned, flags=re.M).strip()
    blocked = ["insert", "update", "delete", "drop", "alter", "truncate", "create", "replace"]
    return cleaned.startswith("select") and not any(re.search(rf"\b{word}\b", cleaned) for word in blocked)


@tool("mysql_tool", args_schema=MysqlSchema)
def mysql_tool(sql: str) -> str:
    """执行只读 MySQL 查询，用于查询 users 和 student_placement(PSEO就业与收入数据) 表。"""
    if not _is_safe_select(sql):
        return "查询被拒绝：只允许执行 SELECT 只读查询"

    try:
        con = pymysql.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "usermessage"),
            charset="utf8mb4",
        )
        cursor = con.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        con.close()
        return str(result)
    except Exception as e:
        logger.warning(f"查询失败：{str(e)}")
        return f"查询失败：{str(e)}"
