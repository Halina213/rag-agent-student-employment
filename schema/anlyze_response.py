from pydantic import BaseModel, Field
class TableResponse(BaseModel):
    """
    表格数据响应类
    """
    column_name: list = Field(..., description="英文表头")
    data: list[dict[str, str]] = Field(..., description="数据")


class AnlyzeResponse(BaseModel):
    """"数据分析响应类"""
    table: TableResponse = Field(..., description="表格数据")
    result: str = Field(..., description="分析结果")
    json: str = Field(..., description="图表数据")
    code: int = Field(..., description="状态码")
    msg: str = Field(..., description="提示信息")
