"""
用户角色权限查询工具

功能说明：
- 根据用户ID（邮箱）查询其在数据库中的角色
- 用于权限验证中间件进行访问控制
- 支持多种角色：总经理、部门经理、员工等

数据库表：
- users 表，包含字段：id, name, email, phone, department, role
"""
from langchain.tools import tool
from schema.mysqlSchema import MysqlSchema
from dotenv import load_dotenv
import os
import pymysql
from utils.Logger import Logger

logger = Logger.get_logger(__name__)
load_dotenv()

def permmision_role(user_id: str) -> str:
    """
    查询用户角色
    
    工作流程：
    1. 构建SQL查询语句
    2. 连接MySQL数据库
    3. 执行查询获取用户角色
    4. 关闭数据库连接并返回结果
    
    参数：
        user_id: 用户邮箱地址
        
    返回：
        str: 用户角色（如"总经理"、"部门经理"、"员工"）
        None: 用户不存在或查询失败
        
    示例：
        >>> permmision_role("767920412@qq.com")
        '总经理'
    """
    # 构建SQL查询语句（使用参数化查询防止SQL注入）
    sql = "SELECT role FROM users WHERE email=%s"
    logger.info(f"执行权限查询SQL: SELECT role FROM users WHERE email={user_id}")
    
    con = None
    cursor = None
    try:
        con = pymysql.connect(
            host=os.getenv("MYSQL_HOST"),
            port=int(os.getenv("MYSQL_PORT")),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE")
        )
        cursor = con.cursor()
        cursor.execute(sql, (user_id,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        return None
    except Exception as e:
        logger.error(f"查询用户角色失败: {str(e)}")
        return None
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
