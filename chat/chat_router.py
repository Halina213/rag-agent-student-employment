import json
import re
import uuid
import time
from fastapi import APIRouter, Request, Form
from utils.Logger import Logger
from fastapi.responses import StreamingResponse, PlainTextResponse
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()
logger = Logger.get_logger(__name__)


def strip_markdown_codeblock(text):
    """剥掉AI返回的 ```json ... ``` 包裹"""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r'^```\w*\n?', '', cleaned)
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
    return cleaned


def _fix_double_braces(text):
    """修复LLM输出双花括号{{}}的问题，转成单花括号{}"""
    if not text or '{{' not in text:
        return text
    # 全局替换双花括号为单花括号（对JSON结构无害，字符串内的{{也会被替换但影响极小）
    fixed = text.replace('{{', '{').replace('}}', '}')
    try:
        json.loads(fixed)
        return fixed
    except:
        return text


def extract_json_from_text(text):
    """从AI返回的文本中提取JSON（可能混合了文字说明和markdown包裹）"""
    if not text:
        return text
    
    text = text.strip()
    
    # 0. 先修复双花括号问题
    text_fixed = _fix_double_braces(text)
    if text_fixed != text:
        text = text_fixed
    
    # 1. 先尝试直接解析
    try:
        json.loads(text)
        return text
    except:
        pass
    
    # 2. 尝试剥掉markdown代码块后解析
    stripped = strip_markdown_codeblock(text)
    try:
        json.loads(stripped)
        return stripped
    except:
        pass
    
    # 3. 用正则从文本中提取 ```json ... ``` 里的内容
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
    if match:
        candidate = match.group(1).strip()
        candidate = _fix_double_braces(candidate)
        try:
            json.loads(candidate)
            return candidate
        except:
            pass
    
    # 4. 从第一个 { 到最后一个 } 尝试解析（支持深层嵌套）
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end+1]
        candidate = _fix_double_braces(candidate)
        try:
            json.loads(candidate)
            return candidate
        except:
            pass
    
    # 5. 都没提取到，返回原始文本
    return text


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


def save_message(user_email, session_id, role, content, chart_option=None, msg_type='text'):
    """保存聊天消息到数据库"""
    try:
        con = get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            "INSERT INTO chat_history (user_email, session_id, role, content, chart_option, msg_type) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_email, session_id, role, content, json.dumps(chart_option, ensure_ascii=False) if chart_option else None, msg_type)
        )
        con.commit()
        cursor.close()
        con.close()
    except Exception as e:
        logger.warn(f"保存消息失败: {e}")


def get_user_info_from_db(email):
    """从数据库获取用户信息"""
    try:
        con = get_db_connection()
        cursor = con.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT name, email, department FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        con.close()
        return user
    except:
        return None


def get_user_preferences(email):
    """获取用户偏好"""
    try:
        con = get_db_connection()
        cursor = con.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT detail_level, default_chart_type FROM user_preferences WHERE user_email = %s", (email,))
        pref = cursor.fetchone()
        cursor.close()
        con.close()
        return pref or {"detail_level": "normal", "default_chart_type": "bar"}
    except:
        return {"detail_level": "normal", "default_chart_type": "bar"}


# 创建聊天路由
chat_router = APIRouter()

# 智能体路由关键词映射
ECHAT_KEYWORDS = ["图表", "图", "画", "可视化", "柱状图", "饼图", "折线图", "散点图", "雷达图", "echart", "chart", "生成图", "绘图"]
ANLYZE_KEYWORDS = ["数据分析", "分析", "统计", "报告", "总结", "趋势"]


def is_valid_chart_option(text):
    """判断文本是否为可渲染的 ECharts option。"""
    try:
        obj = json.loads(text)
        series = obj.get("series")
        return bool(series and isinstance(series, list) and len(series) > 0)
    except Exception:
        return False


def build_pseo_bar_chart(question: str):
    """当模型图表生成失败时，直接用数据库结果生成 PSEO 柱状图。"""
    q = question.lower()

    if "10年" in question or "10 年" in question:
        metric = "median_earnings_10yr"
        metric_name = "毕业后10年收入中位数"
    elif "5年" in question or "5 年" in question:
        metric = "median_earnings_5yr"
        metric_name = "毕业后5年收入中位数"
    else:
        metric = "median_earnings_1yr"
        metric_name = "毕业后1年收入中位数"

    if "专业大类" in question or "专业方向" in question or "专业" in question:
        dimension = "major_category"
        dimension_name = "专业大类"
    elif "学校" in question or "院校" in question:
        dimension = "institution_name"
        dimension_name = "学校"
    elif "州" in question or "地区" in question:
        dimension = "institution_state"
        dimension_name = "地区"
    elif "行业" in question:
        dimension = "industry"
        dimension_name = "行业"
    else:
        dimension = "degree_level"
        dimension_name = "学历层级"

    sql = f"""
        SELECT `{dimension}` AS label, ROUND(AVG(`{metric}`), 2) AS value
        FROM student_placement
        WHERE `{dimension}` IS NOT NULL
          AND `{dimension}` <> ''
          AND `{metric}` IS NOT NULL
          AND `{metric}` > 0
        GROUP BY `{dimension}`
        ORDER BY value DESC
        LIMIT 10
    """

    con = get_db_connection()
    cursor = con.cursor()
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
    finally:
        cursor.close()
        con.close()

    if not rows:
        return None

    labels = [str(row[0]) for row in rows]
    values = [float(row[1]) for row in rows]

    return {
        "title": {"text": f"📊 不同{dimension_name}的{metric_name}"},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "toolbox": {"feature": {"saveAsImage": {}}},
        "grid": {"left": "8%", "right": "6%", "bottom": "18%", "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": labels,
            "axisLabel": {"rotate": 30, "interval": 0}
        },
        "yAxis": {
            "type": "value",
            "name": "美元",
            "axisLabel": {"formatter": "${value}"}
        },
        "series": [{
            "name": metric_name,
            "type": "bar",
            "data": values,
            "itemStyle": {"color": "#5470C6"},
            "label": {"show": True, "position": "top", "formatter": "${c}"}
        }]
    }


@chat_router.post("/chat")
async def chat(request: Request, question: str = Form(...), user_id: str = Form(...), session_id: str = Form(None)):
    q = question.lower()
    
    # 生成或使用已有的session_id
    sid = session_id or str(uuid.uuid4())[:8]
    
    # 获取用户信息，构建个性化上下文
    user_info = get_user_info_from_db(user_id)
    user_prefs = get_user_preferences(user_id)
    user_context = ""
    if user_info:
        user_context = f"[当前用户信息] 姓名：{user_info['name']}，学院/部门：{user_info.get('department', '未知')}，邮箱：{user_info['email']}"
    detail_instruction = {
        "simple": "回答要简洁，控制在3句话以内",
        "normal": "正常详细程度回答",
        "detailed": "回答要详细，提供充分的数据支撑和深度分析"
    }.get(user_prefs.get("detail_level", "normal"), "正常详细程度回答")
    
    # 保存用户消息
    save_message(user_id, sid, "user", question)
    
    # 图表智能体
    if any(kw in q for kw in ECHAT_KEYWORDS):
        echarts_agent = request.app.state.echarts_agent
        # 注入用户上下文
        personalized_question = f"{user_context}\n{detail_instruction}\n用户问题：{question}" if user_context else question
        result = echarts_agent.answer(personalized_question, user_id)
        extracted = extract_json_from_text(result)
        logger.info(f"[图表路由] 原始返回长度: {len(result)}, 提取后长度: {len(extracted)}")
        if not is_valid_chart_option(extracted):
            logger.warn("[图表路由] 模型未返回有效图表配置，使用本地PSEO柱状图兜底")
            fallback_chart = build_pseo_bar_chart(question)
            if fallback_chart:
                extracted = json.dumps(fallback_chart, ensure_ascii=False)
        # 保存AI消息
        save_message(user_id, sid, "ai", extracted, msg_type='chart')
        return PlainTextResponse(content=extracted, media_type="application/json")
    
    # 数据分析智能体
    elif any(kw in q for kw in ANLYZE_KEYWORDS):
        anlyze_agent = request.app.state.anlyze_agent
        personalized_question = f"{user_context}\n{detail_instruction}\n用户问题：{question}" if user_context else question
        result = anlyze_agent.answer(personalized_question, user_id)
        extracted = extract_json_from_text(result)
        logger.info(f"[分析路由] 原始返回长度: {len(result)}, 提取后长度: {len(extracted)}")
        # 尝试解析出chart部分单独保存
        chart_opt = None
        try:
            obj = json.loads(extracted)
            if obj.get("chart"):
                chart_opt = obj["chart"]
        except:
            pass
        save_message(user_id, sid, "ai", extracted, chart_option=chart_opt, msg_type='analysis')
        return PlainTextResponse(content=extracted, media_type="application/json")

    # 默认：SQL问答智能体（SSE流式）
    current_use_agent = request.app.state.sql_question_agent_pg
    personalized_question = f"{user_context}\n{detail_instruction}\n用户问题：{question}" if user_context else question

    # 用来收集完整回复
    full_response = []

    async def generator():
        try:
            method = getattr(current_use_agent, "answer", getattr(current_use_agent, "stream", None))
            async for chunk in method(personalized_question, user_id):
                chunk = strip_markdown_codeblock(chunk)
                full_response.append(chunk)
                msg = {"content": chunk, "done": False}
                yield f"data:{json.dumps(msg, ensure_ascii=False)}\n\n"
            
            # 保存完整AI回复
            complete_response = "".join(full_response)
            save_message(user_id, sid, "ai", complete_response)
            
            msg = {"content": "", "done": True, "session_id": sid}
            yield f"data:{json.dumps(msg, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.warn(f"错误信息：{str(e)}")
            msg = {"content": "出错了", "done": True, "error": True}
            yield f"data:{json.dumps(msg, ensure_ascii=False)}\n\n"

    return StreamingResponse(content=generator(), media_type="text/event-stream")


@chat_router.get("/chat_history")
def get_chat_history(email: str, session_id: str = None, limit: int = 50):
    """获取聊天记录"""
    try:
        con = get_db_connection()
        cursor = con.cursor(pymysql.cursors.DictCursor)
        
        if session_id:
            cursor.execute(
                "SELECT id, role, content, chart_option, msg_type, created_at FROM chat_history WHERE user_email = %s AND session_id = %s ORDER BY created_at ASC LIMIT %s",
                (email, session_id, limit)
            )
        else:
            # 获取最近的一个session的记录
            cursor.execute(
                "SELECT session_id FROM chat_history WHERE user_email = %s ORDER BY created_at DESC LIMIT 1",
                (email,)
            )
            latest = cursor.fetchone()
            if latest:
                cursor.execute(
                    "SELECT id, role, content, chart_option, msg_type, created_at FROM chat_history WHERE user_email = %s AND session_id = %s ORDER BY created_at ASC LIMIT %s",
                    (email, latest["session_id"], limit)
                )
            else:
                cursor.close()
                con.close()
                return {"code": 200, "data": []}
        
        rows = cursor.fetchall()
        cursor.close()
        con.close()
        
        # 解析chart_option
        for row in rows:
            if row.get("chart_option") and isinstance(row["chart_option"], str):
                try:
                    row["chart_option"] = json.loads(row["chart_option"])
                except:
                    row["chart_option"] = None
        
        return {"code": 200, "data": rows}
    except Exception as e:
        logger.warn(f"获取聊天记录失败: {e}")
        return {"code": 500, "msg": "获取聊天记录失败"}


@chat_router.get("/sessions")
def get_sessions(email: str):
    """获取用户的会话列表"""
    try:
        con = get_db_connection()
        cursor = con.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            "SELECT session_id, MIN(created_at) as created_at, MAX(created_at) as last_active, COUNT(*) as msg_count FROM chat_history WHERE user_email = %s GROUP BY session_id ORDER BY last_active DESC",
            (email,)
        )
        sessions = cursor.fetchall()
        cursor.close()
        con.close()
        return {"code": 200, "data": sessions}
    except Exception as e:
        logger.warn(f"获取会话列表失败: {e}")
        return {"code": 500, "msg": "获取会话列表失败"}


from fastapi import UploadFile, File

@chat_router.post("/upload")
async def upload(file: UploadFile = File(...)):
    UPLOAD_DIR = "static/upload"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    logger.info(f"上传文件：{file_path}")
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        from utils.file_importer import import_file_to_db
        import_result = import_file_to_db(file_path, file.filename)
    except Exception as e:
        logger.warn(f"导入文件失败: {str(e)}")
        import_result = {"success": False, "error": str(e)}

    return {
        "code": 200,
        "filename": file.filename,
        "import_result": import_result
    }
