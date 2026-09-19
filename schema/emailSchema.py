from pydantic import BaseModel,Field

#定义一个邮箱工具参数

class EmailSchema(BaseModel):
    #...必须要传
    to: str = Field(...,description="收件人邮箱")
    subject: str = Field(...,description="邮件主题")
    content: str = Field(...,description="邮件内容")
