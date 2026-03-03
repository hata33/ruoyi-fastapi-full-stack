"""
聊天模块通用 VO（View Object）

说明：
- 定义通用的响应模型
- 提供统一的操作结果返回格式
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Optional


class CrudResponseModel(BaseModel):
    """
    操作响应模型
    """
    is_success: bool = Field(description='操作是否成功')
    message: str = Field(description='响应信息')
    result: Optional[Any] = Field(default=None, description='响应结果')
