from pydantic import BaseModel, Field


#定义一个类作为输出格式
class EchartsResponse(BaseModel):
    chart_data: str = Field(..., description="echarts图表的JSON配置数据", alias="json")
    code: int = Field(..., description="状态码，200表示成功，500表示失败")
    msg: str = Field(..., description="提示信息")
