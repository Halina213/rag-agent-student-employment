# 定义数据验证模型
from pydantic import BaseModel,Field
# Pydantic 是一个数据验证和设置管理库，常用于 FastAPI 项目
class MysqlSchema(BaseModel):
    sql: str = Field(...,description="mysql语句")
# description：用于存储 MySQL 查询语句
