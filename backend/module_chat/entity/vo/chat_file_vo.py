"""
聊天文件上传 VO（View Object）

说明：
- 定义文件上传相关的请求/响应模型
- 包括文件上传、列表查询、删除等
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from typing import List, Optional


class ChatFileModel(BaseModel):
    """
    聊天文件表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    file_id: Optional[int] = Field(default=None, description='文件ID')
    file_name: Optional[str] = Field(default=None, description='文件名')
    file_path: Optional[str] = Field(default=None, description='文件路径')
    file_type: Optional[str] = Field(default=None, description='文件类型')
    file_size: Optional[int] = Field(default=None, description='文件大小')
    conversation_id: Optional[int] = Field(default=None, description='关联会话ID')
    message_id: Optional[int] = Field(default=None, description='关联消息ID')
    user_id: Optional[int] = Field(default=None, description='用户ID')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')


class ChatFileQueryModel(BaseModel):
    """
    文件查询模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    file_type: Optional[str] = Field(default=None, description='文件类型')
    conversation_id: Optional[int] = Field(default=None, description='会话ID')
    user_id: Optional[int] = Field(default=None, description='用户ID')


class ChatFilePageQueryModel(ChatFileQueryModel):
    """
    文件分页查询模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=20, description='每页记录数')


class DeleteChatFileModel(BaseModel):
    """
    删除文件模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    file_ids: str = Field(description='需要删除的文件ID')
