from pydantic import BaseModel,Field
"""
发送验证码接口参数模型类
"""
class SendCodeSchema(BaseModel):
    email: str = Field(..., description="邮箱")


"""
登录验证码接口参数模型类
"""
class LoginSchema(BaseModel):
    email: str = Field(..., description="邮箱")
    code: str = Field(..., description="验证码")
