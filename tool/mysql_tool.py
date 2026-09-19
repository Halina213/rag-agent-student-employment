import os
import re
import pymysql
import sqlparse
from dotenv import load_dotenv
from langchain.tools import tool
from schema.mysqlSchema import MysqlSchema
from utils.Logger import Logger

load_dotenv()
logger = Logger.get_logger(__name__)

_BLOCKED = {"insert", "update", "delete", "drop", "alter", "truncate", "create", "replace", "grant"}


def _is_safe_select(sql: str) -> bool:
    """只允许单条 SELECT 语句。用 sqlparse 解析，比纯正则更可靠。"""
    statements = [s for s in sqlparse.parse(sql) if str(s).strip()]
    if len(statements) != 1:
        return False
    if statements[0].get_type() != "SELECT":
        return False
    lowered = sql.lower()
    return not any(re.search(rf"\b{w}\b", lowered) for w in _BLOCKED)


def _enforce_limit(sql: str, default_limit: int = 200) -> str:
    """没有 LIMIT 就补一个，防止一次性拉回海量数据。"""
    if re.search(r"\blimit\b", sql, re.IGNORECASE):
        return sql
    return f"{sql.rstrip().rstrip(';')} LIMIT {default_limit}"


@tool("mysql_tool", args_schema=MysqlSchema)
def mysql_tool(sql: str) -> str:
    """执行只读 MySQL 查询，用于查询 users 和 student_placement(PSEO就业与收入数据) 表。"""
    if not _is_safe_select(sql):
        return "查询被拒绝：只允许执行单条 SELECT 只读查询。请修正后重试。"

    sql = _enforce_limit(sql)
    try:
        con = pymysql.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "usermessage"),
            charset="utf8mb4",
            connect_timeout=5,
            read_timeout=15,
        )

        cursor = con.cursor()
        logger.info(f"[Text-to-SQL] 执行: {sql}")
        cursor.execute(sql)
        rows = cursor.fetchall()
        cursor.close()
        con.close()
        return f"执行SQL: {sql}\n结果({len(rows)}行): {rows}"
    except Exception as e:
        logger.warning(f"查询失败：{str(e)}")
        return f"查询失败：{str(e)}。请根据错误信息修正 SQL 后重试。"