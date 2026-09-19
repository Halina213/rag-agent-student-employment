"""
文件导入工具
支持 CSV 和 Excel 文件导入到 MySQL 数据库。
当前业务表已适配 PSEO 高校毕业生就业与收入数据。
"""

import os
from pathlib import Path

import pymysql
from dotenv import load_dotenv
from utils.Logger import Logger
from import_data import PSEO_COLUMNS, load_pseo_dataframe

# 加载环境变量
load_dotenv()

logger = Logger.get_logger(__name__)

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        charset='utf8mb4'
    )


def import_file_to_db(file_path: str, filename: str) -> dict:
    """
    将 CSV/Excel 文件导入到 student_placement 表（PSEO数据）
    
    Args:
        file_path: 文件完整路径
        filename: 文件名
        
    Returns:
        {"success": True, "rows": 数量} 或 {"success": False, "error": "错误信息"}
    """
    try:
        # 获取文件扩展名
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext not in ['.csv', '.xlsx', '.xls']:
            return {"success": False, "error": f"不支持的文件格式: {file_ext}"}

        df = load_pseo_dataframe(Path(file_path))
        
        # 连接到数据库
        con = get_db_connection()
        cursor = con.cursor()
        
        try:
            # 清空表（避免数据重复）
            cursor.execute("TRUNCATE TABLE student_placement")
            logger.info(f"已清空 student_placement 表")
            
            # 构建 INSERT 语句
            placeholders = ', '.join(['%s'] * len(PSEO_COLUMNS))
            insert_sql = f"INSERT INTO student_placement ({', '.join(PSEO_COLUMNS)}) VALUES ({placeholders})"
            
            # 批量插入
            rows_to_insert = [tuple(row) for row in df[PSEO_COLUMNS].itertuples(index=False, name=None)]
            cursor.executemany(insert_sql, rows_to_insert)
            
            # 提交事务
            con.commit()
            
            rows_count = len(df)
            logger.info(f"成功导入 {rows_count} 条 PSEO 数据到 student_placement 表")
            
            return {"success": True, "rows": rows_count}
            
        except Exception as e:
            con.rollback()
            logger.warn(f"数据库导入失败: {str(e)}")
            return {"success": False, "error": f"数据库导入失败: {str(e)}"}
            
        finally:
            cursor.close()
            con.close()
            
    except Exception as e:
        logger.warn(f"文件导入失败: {str(e)}")
        return {"success": False, "error": str(e)}
