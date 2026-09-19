from utils.Logger import Logger
from typing import Callable, Any, Dict, Union
import os
from dotenv import load_dotenv

# 加载配置
load_dotenv()
# 初始化日志
logger = Logger.get_logger(__name__)

# 权限配置（可从数据库/配置文件读取，这里示例用硬编码）
# 1. 用户白名单（示例）
_allowed_ids = {"2972526358@qq.com", "3082686649@qq.com"}
# 可扩展：从环境变量加载
_extra_ids = os.getenv("ALLOWED_USER_IDS", "")
if _extra_ids:
    _allowed_ids.update(_extra_ids.split(","))
ALLOWED_USER_IDS = _allowed_ids

# 2. 允许查询的表名（防止查询敏感表）
ALLOWED_TABLES = {"sales_data", "product_info", "user_behavior"}


def before_agent_middleware(params: Dict[str, Any], call_next: Callable) -> Any:
    """
    智能体执行前的权限校验中间件
    :param params: langgraph 上下文参数（包含用户ID、用户提问等）
    :param call_next: 下一步执行的函数（继续执行智能体逻辑）
    :return: 校验通过则执行下一步，否则抛出异常/返回权限错误
    """
    try:
        # ========== 1. 提取上下文关键信息 ==========
        # 从 messages 中提取用户ID和提问内容
        messages = params.get("messages", [])
        user_id = None
        user_question = None
        for msg in messages:
            if hasattr(msg, "user_id"):
                user_id = msg.user_id
            if hasattr(msg, "content"):
                user_question = msg.content

        # 基础校验：用户ID不能为空
        if not user_id:
            raise PermissionError("用户ID不能为空，权限校验失败")

        logger.info(f"开始校验用户 {user_id} 的操作权限")

        # ========== 2. 用户身份校验（白名单） ==========
        if user_id not in ALLOWED_USER_IDS:
            raise PermissionError(f"用户 {user_id} 无操作权限，请联系管理员")

        # ========== 3. 敏感操作/数据校验（可选） ==========
        # 示例：禁止查询敏感表/关键词
        sensitive_keywords = ["user_password", "admin", "salary", "敏感表名"]
        if user_question and any(keyword in user_question for keyword in sensitive_keywords):
            raise PermissionError(f"提问包含敏感关键词，禁止执行：{user_question}")

        # ========== 4. 校验通过，执行下一步 ==========
        logger.info(f"用户 {user_id} 权限校验通过，继续执行智能体逻辑")
        return call_next(params)

    except PermissionError as e:
        # 权限错误日志 + 返回标准化错误
        logger.error(f"权限校验失败：{str(e)}")
        return {
            "code": 403,
            "msg": f"权限校验失败：{str(e)}",
            "data": None
        }
    except Exception as e:
        # 其他异常捕获
        logger.error(f"权限中间件执行异常：{str(e)}")
        return {
            "code": 500,
            "msg": f"权限校验异常：{str(e)}",
            "data": None
        }


# 扩展：可选的后置中间件（如果需要校验返回结果）
def after_agent_middleware(params: Dict[str, Any], call_next: Callable) -> Any:
    """
    智能体执行后的权限校验（如过滤敏感返回数据）
    """
    # 先执行智能体逻辑
    result = call_next(params)
    # 过滤敏感数据（示例）
    if isinstance(result, dict) and "data" in result:
        # 示例：移除返回结果中的敏感字段
        sensitive_fields = ["password", "phone", "id_card"]
        for field in sensitive_fields:
            result["data"].pop(field, None)
    return result
