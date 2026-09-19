from fastapi import APIRouter, Request
from schema.Login_schema import SendCodeSchema, LoginSchema
from utils.Logger import Logger
from chat.chat_router import extract_json_from_text
import json
import pymysql
import os
import time
from dotenv import load_dotenv

load_dotenv()
system_router = APIRouter()
logger = Logger.get_logger(__name__)

# 使用内存保存验证码，避免本地开发必须安装 Redis。
# 结构：{"邮箱": {"code": "1234", "expire_at": 时间戳}}
code_cache = {}
CODE_EXPIRE_SECONDS = 300


def get_db_connection():
    """获取MySQL数据库连接"""
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        charset='utf8mb4'
    )


@system_router.post("/send_code")
def send_code(request: Request, args: SendCodeSchema):
    agent = request.app.state.system_agent
    rs = agent.answer(args.email)
    
    # 统一用 extract_json_from_text 解析AI返回
    if isinstance(rs, str):
        extracted = extract_json_from_text(rs)
        try:
            rs = json.loads(extracted)
        except json.JSONDecodeError:
            return {"code": 500, "msg": "验证码发送失败，AI返回格式异常"}
    
    if rs.get("code") in ("200", 200):
        code_cache[args.email] = {
            "code": str(rs["data"]),
            "expire_at": time.time() + CODE_EXPIRE_SECONDS
        }
        logger.info("验证码发送成功，已保存到内存缓存")
        return {"code": 200, "msg": "验证码发送成功"}
    else:
        logger.warning(f"验证码发送失败：{rs.get('msg')}")
        return {"code": 500, "msg": rs.get("msg", "发送失败")}


@system_router.post("/login")
def login(args: LoginSchema):
    logger.info(f"登录验证：{args.email}")
    try:
        stored = code_cache.get(args.email)
        if not stored:
            return {"code": 500, "msg": "验证码已过期，请重新获取"}
        if time.time() > stored["expire_at"]:
            code_cache.pop(args.email, None)
            return {"code": 500, "msg": "验证码已过期，请重新获取"}
        code = stored["code"]
        if code != args.code:
            return {"code": 500, "msg": "验证码错误"}
        
        # 验证码正确，查询用户信息
        try:
            con = get_db_connection()
            cursor = con.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT id, name, email, phone, department, avatar FROM users WHERE email = %s", (args.email,))
            user = cursor.fetchone()
            
            # 更新最后登录时间
            cursor.execute("UPDATE users SET last_login = NOW() WHERE email = %s", (args.email,))
            con.commit()
            cursor.close()
            con.close()
        except Exception as e:
            logger.warn(f"查询用户信息失败: {e}")
            user = None
        
        # 查询用户偏好
        preferences = {"detail_level": "normal", "default_chart_type": "bar", "theme": "light"}
        try:
            con = get_db_connection()
            cursor = con.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT detail_level, default_chart_type, theme FROM user_preferences WHERE user_email = %s", (args.email,))
            pref = cursor.fetchone()
            cursor.close()
            con.close()
            if pref:
                preferences = pref
        except Exception as e:
            logger.warn(f"查询用户偏好失败: {e}")
        
        if user:
            # 删除验证码
            code_cache.pop(args.email, None)
            return {
                "code": 200, 
                "msg": "登陆成功",
                "data": {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "phone": user.get("phone", ""),
                    "department": user.get("department", ""),
                    "avatar": user.get("avatar", ""),
                    "preferences": preferences
                }
            }
        else:
            return {"code": 200, "msg": "登陆成功", "data": {"email": args.email, "name": args.email.split('@')[0], "preferences": preferences}}
            
    except Exception as e:
        logger.warn(f"登录异常：{e}")
        return {"code": 500, "msg": "登录失败，请重试"}


@system_router.get("/user_info")
def get_user_info(email: str):
    """获取用户信息接口"""
    try:
        con = get_db_connection()
        cursor = con.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT id, name, email, phone, department, avatar FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        con.close()
        
        if user:
            return {"code": 200, "data": user}
        return {"code": 404, "msg": "用户不存在"}
    except Exception as e:
        logger.warn(f"获取用户信息失败: {e}")
        return {"code": 500, "msg": "获取用户信息失败"}


@system_router.post("/update_preferences")
def update_preferences(email: str, detail_level: str = None, default_chart_type: str = None, theme: str = None):
    """更新用户偏好设置"""
    try:
        con = get_db_connection()
        cursor = con.cursor()
        
        # 先检查是否已有偏好记录
        cursor.execute("SELECT id FROM user_preferences WHERE user_email = %s", (email,))
        exists = cursor.fetchone()
        
        if exists:
            # 更新
            updates = []
            params = []
            if detail_level:
                updates.append("detail_level = %s")
                params.append(detail_level)
            if default_chart_type:
                updates.append("default_chart_type = %s")
                params.append(default_chart_type)
            if theme:
                updates.append("theme = %s")
                params.append(theme)
            
            if updates:
                sql = f"UPDATE user_preferences SET {', '.join(updates)} WHERE user_email = %s"
                params.append(email)
                cursor.execute(sql, params)
        else:
            # 新建
            cursor.execute(
                "INSERT INTO user_preferences (user_email, detail_level, default_chart_type, theme) VALUES (%s, %s, %s, %s)",
                (email, detail_level or 'normal', default_chart_type or 'bar', theme or 'light')
            )
        
        con.commit()
        cursor.close()
        con.close()
        return {"code": 200, "msg": "偏好更新成功"}
    except Exception as e:
        logger.warn(f"更新偏好失败: {e}")
        return {"code": 500, "msg": "更新偏好失败"}
