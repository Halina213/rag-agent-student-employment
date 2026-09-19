"""
数据库初始化脚本
用于创建 MySQL 数据库表结构

【功能】
1. 创建 users 表（登录验证用）
2. 创建 student_placement 表（PSEO 高校毕业生就业与收入数据）
3. 创建 chat_history 表（聊天记录持久化）
4. 创建 user_preferences 表（用户偏好设置）
5. 插入测试用户数据到 users 表

【使用】
python init_db.py
"""

import pymysql
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def init_database():
    """初始化数据库表结构"""
    
    # 连接MySQL数据库
    con = pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        charset='utf8mb4'
    )
    
    cursor = con.cursor()
    database_name = os.getenv("MYSQL_DATABASE")
    
    try:
        # 创建数据库（如果不存在）
        print(f"创建数据库 {database_name}（如果不存在）...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"USE `{database_name}`")
        print(f"✓ 数据库 {database_name} 就绪")
        
        # ============================================
        # 1. 创建 users 表（登录验证用）
        # ============================================
        print("\n创建 users 表（用户表）...")
        users_table_sql = """
        CREATE TABLE IF NOT EXISTS `users` (
            `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
            `name` VARCHAR(50) NOT NULL COMMENT '用户姓名',
            `email` VARCHAR(100) NOT NULL UNIQUE COMMENT '用户邮箱',
            `phone` VARCHAR(20) DEFAULT NULL COMMENT '用户电话',
            `department` VARCHAR(50) DEFAULT NULL COMMENT '部门',
            `avatar` VARCHAR(255) DEFAULT NULL COMMENT '头像URL',
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            `last_login` TIMESTAMP NULL DEFAULT NULL COMMENT '最后登录时间',
            INDEX `idx_email` (`email`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';
        """
        cursor.execute(users_table_sql)
        print("✓ users 表创建成功")
        
        # ============================================
        # 2. 创建 student_placement 表（PSEO 高校毕业生就业与收入数据）
        # ============================================
        print("\n重建 student_placement 表（PSEO 高校毕业生就业与收入数据表）...")
        cursor.execute("DROP TABLE IF EXISTS `student_placement`")
        student_table_sql = """
        CREATE TABLE `student_placement` (
            `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
            `institution_id` VARCHAR(50) DEFAULT NULL COMMENT '学校/机构ID',
            `institution_name` VARCHAR(255) DEFAULT NULL COMMENT '学校/机构名称',
            `institution_state` VARCHAR(50) DEFAULT NULL COMMENT '学校所在州/地区',
            `institution_type` VARCHAR(100) DEFAULT NULL COMMENT '学校类型或层级',
            `degree_level` VARCHAR(100) DEFAULT NULL COMMENT '学历层级，如Certificate/Associate/Bachelor/Master/Doctoral',
            `degree_field` VARCHAR(255) DEFAULT NULL COMMENT '专业/学科字段',
            `major_category` VARCHAR(255) DEFAULT NULL COMMENT '专业大类',
            `graduation_year` INT DEFAULT NULL COMMENT '毕业年份',
            `cohort_year` VARCHAR(50) DEFAULT NULL COMMENT '毕业 cohort/统计批次',
            `industry` VARCHAR(255) DEFAULT NULL COMMENT '就业行业',
            `employment_count` INT DEFAULT NULL COMMENT '就业人数',
            `total_graduates` INT DEFAULT NULL COMMENT '毕业生人数/样本人数',
            `employment_rate` DOUBLE DEFAULT NULL COMMENT '就业率，百分比数值0-100',
            `median_earnings_1yr` DOUBLE DEFAULT NULL COMMENT '毕业后1年收入中位数',
            `median_earnings_5yr` DOUBLE DEFAULT NULL COMMENT '毕业后5年收入中位数',
            `median_earnings_10yr` DOUBLE DEFAULT NULL COMMENT '毕业后10年收入中位数',
            `p25_earnings` DOUBLE DEFAULT NULL COMMENT '收入第25百分位',
            `p75_earnings` DOUBLE DEFAULT NULL COMMENT '收入第75百分位',
            `source_file` VARCHAR(255) DEFAULT NULL COMMENT '导入来源文件名',
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '导入时间',
            INDEX `idx_institution` (`institution_name`),
            INDEX `idx_state` (`institution_state`),
            INDEX `idx_degree_level` (`degree_level`),
            INDEX `idx_degree_field` (`degree_field`),
            INDEX `idx_industry` (`industry`),
            INDEX `idx_graduation_year` (`graduation_year`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='PSEO 高校毕业生就业与收入数据表';
        """
        cursor.execute(student_table_sql)
        print("✓ student_placement 表创建成功")
        
        # ============================================
        # 3. 创建 chat_history 表（聊天记录持久化）
        # ============================================
        print("\n创建 chat_history 表（聊天记录表）...")
        chat_history_sql = """
        CREATE TABLE IF NOT EXISTS `chat_history` (
            `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
            `user_email` VARCHAR(100) NOT NULL COMMENT '用户邮箱',
            `session_id` VARCHAR(50) NOT NULL COMMENT '会话ID',
            `role` VARCHAR(10) NOT NULL COMMENT '角色: user/ai',
            `content` TEXT COMMENT '消息内容',
            `chart_option` JSON DEFAULT NULL COMMENT 'ECharts图表配置(JSON)',
            `msg_type` VARCHAR(20) DEFAULT 'text' COMMENT '消息类型: text/chart/analysis',
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            INDEX `idx_user_email` (`user_email`),
            INDEX `idx_session_id` (`session_id`),
            INDEX `idx_created_at` (`created_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聊天记录表';
        """
        cursor.execute(chat_history_sql)
        print("✓ chat_history 表创建成功")
        
        # ============================================
        # 4. 创建 user_preferences 表（用户偏好设置）
        # ============================================
        print("\n创建 user_preferences 表（用户偏好表）...")
        user_preferences_sql = """
        CREATE TABLE IF NOT EXISTS `user_preferences` (
            `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '偏好ID',
            `user_email` VARCHAR(100) NOT NULL UNIQUE COMMENT '用户邮箱',
            `detail_level` VARCHAR(10) DEFAULT 'normal' COMMENT '回答详细程度: simple/normal/detailed',
            `default_chart_type` VARCHAR(20) DEFAULT 'bar' COMMENT '默认图表类型: bar/line/pie/scatter',
            `theme` VARCHAR(10) DEFAULT 'light' COMMENT '界面主题: light/dark',
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            INDEX `idx_user_email` (`user_email`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户偏好设置表';
        """
        cursor.execute(user_preferences_sql)
        print("✓ user_preferences 表创建成功")
        
        # ============================================
        # 5. 插入测试用户数据
        # ============================================
        print("\n插入测试用户数据...")
        test_users = [
            ('杨小雨', '3493985772@qq.com', '13800138001', '人工智能与大数据学院'),
            ('张三', 'zhangsan@example.com', '13800138002', '计算机科学学院'),
            ('李四', 'lisi@example.com', '13800138003', '经济管理学院'),
            ('王五', 'wangwu@example.com', '13800138004', '电子信息学院'),
        ]
        
        for name, email, phone, department in test_users:
            try:
                cursor.execute(
                    "INSERT IGNORE INTO `users` (`name`, `email`, `phone`, `department`) VALUES (%s, %s, %s, %s)",
                    (name, email, phone, department)
                )
            except Exception as e:
                print(f"  插入用户 {name} 失败: {e}")
        
        print("✓ 测试用户数据插入完成")
        
        # 提交事务
        con.commit()
        print("\n" + "="*50)
        print("✅ 数据库初始化完成！")
        print(f"  - users 表（用户表）")
        print(f"  - student_placement 表（PSEO就业与收入数据表）")
        print(f"  - chat_history 表（聊天记录表）")
        print(f"  - user_preferences 表（用户偏好表）")
        print("="*50)
        
    except Exception as e:
        con.rollback()
        print(f"\n❌ 数据库初始化失败: {e}")
        raise
    finally:
        cursor.close()
        con.close()


if __name__ == "__main__":
    init_database()
