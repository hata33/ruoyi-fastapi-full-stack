"""
聊天消息管理 VO（View Object）

说明：
- 定义消息管理相关的请求/响应模型
- 包括发送消息、流式输出、停止生成等
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size
from typing import List, Optional, Literal


class ChatMessageModel(BaseModel):
    """
    聊天消息表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    message_id: Optional[int] = Field(default=None, description='消息ID')
    conversation_id: Optional[int] = Field(default=None, description='会话ID')
    role: Optional[Literal['user', 'assistant', 'system']] = Field(default=None, description='角色')
    content: Optional[str] = Field(default=None, description='消息内容')
    thinking_content: Optional[str] = Field(default=None, description='推理过程内容')
    tokens_used: Optional[int] = Field(default=None, description='使用的token数')
    attachments: Optional[List[int]] = Field(default=None, description='附件ID列表')
    user_id: Optional[int] = Field(default=None, description='用户ID')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')

    @NotBlank(field_name='content', message='消息内容不能为空')
    def get_content(self):
        return self.content

    def validate_fields(self):
        self.get_content()


class SendMessageModel(BaseModel):
    """
    发送消息模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    conversation_id: int = Field(description='会话ID')
    content: str = Field(description='消息内容')
    model_id: Optional[str] = Field(default=None, description='模型ID')
    enable_search: Optional[bool] = Field(default=False, description='是否启用联网搜索')
    attachments: Optional[List[int]] = Field(default=None, description='附件ID列表')
    temperature: Optional[float] = Field(default=None, description='温度参数')
    top_p: Optional[float] = Field(default=None, description='采样参数')
    max_tokens: Optional[int] = Field(default=None, description='最大生成token数')


class RegenerateMessageModel(BaseModel):
    """
    重新生成消息模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    model_id: Optional[str] = Field(default=None, description='新的模型ID')
    temperature: Optional[float] = Field(default=None, description='温度参数')
    top_p: Optional[float] = Field(default=None, description='采样参数')
    max_tokens: Optional[int] = Field(default=None, description='最大生成token数')


class MessageListModel(BaseModel):
    """
    消息列表模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    rows: List[ChatMessageModel] = Field(default_factory=list, description='消息列表')
    total: int = Field(description='总记录数')
    has_more: bool = Field(default=False, description='是否有更多数据')


class StreamMessageModel(BaseModel):
    """
    流式消息事件模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    event_type: Literal['message_start', 'content_delta', 'thinking_start', 'thinking_delta',
                         'thinking_end', 'message_end', 'error'] = Field(description='事件类型')
    message_id: Optional[int] = Field(default=None, description='消息ID')
    content: Optional[str] = Field(default=None, description='内容增量')
    tokens_used: Optional[int] = Field(default=None, description='使用的token数')
    total_tokens: Optional[int] = Field(default=None, description='累计token数')
    error: Optional[str] = Field(default=None, description='错误信息')
