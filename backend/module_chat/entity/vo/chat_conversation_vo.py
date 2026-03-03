"""
聊天会话管理 VO（View Object）

说明：
- 定义会话管理相关的请求/响应模型
- 包括会话列表、详情、创建、更新等
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size
from typing import List, Optional, Literal


class ChatConversationModel(BaseModel):
    """
    聊天会话表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    conversation_id: Optional[int] = Field(default=None, description='会话ID')
    title: Optional[str] = Field(default=None, description='会话标题')
    model_id: Optional[str] = Field(default=None, description='模型ID')
    is_pinned: Optional[bool] = Field(default=None, description='是否置顶')
    pin_time: Optional[datetime] = Field(default=None, description='置顶时间')
    tag_list: Optional[List[str]] = Field(default=None, description='标签列表')
    total_tokens: Optional[int] = Field(default=None, description='累计token数')
    message_count: Optional[int] = Field(default=None, description='消息数量')
    user_id: Optional[int] = Field(default=None, description='用户ID')
    create_by: Optional[str] = Field(default=None, description='创建者')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')
    remark: Optional[str] = Field(default=None, description='备注')

    @NotBlank(field_name='title', message='会话标题不能为空')
    @Size(field_name='title', min_length=0, max_length=50, message='会话标题不能超过50个字符')
    def get_title(self):
        return self.title

    def validate_fields(self):
        self.get_title()


class ChatConversationQueryModel(BaseModel):
    """
    会话查询模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    conversation_id: Optional[int] = Field(default=None, description='会话ID')
    title: Optional[str] = Field(default=None, description='会话标题')
    model_id: Optional[str] = Field(default=None, description='模型ID')
    is_pinned: Optional[bool] = Field(default=None, description='是否置顶')
    tag_id: Optional[int] = Field(default=None, description='标签ID')
    user_id: Optional[int] = Field(default=None, description='用户ID')
    begin_time: Optional[str] = Field(default=None, description='开始时间')
    end_time: Optional[str] = Field(default=None, description='结束时间')


class ChatConversationPageQueryModel(ChatConversationQueryModel):
    """
    会话分页查询模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=20, description='每页记录数')


class AddChatConversationModel(BaseModel):
    """
    新增会话模型
    """
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

    model_id: Optional[str] = Field(default='deepseek-chat', alias='modelId', description='模型ID')
    title: Optional[str] = Field(default='新对话', alias='title', description='会话标题')
    tag_list: Optional[List[str]] = Field(default=None, alias='tagList', description='标签列表')


class UpdateChatConversationModel(BaseModel):
    """
    更新会话模型
    """
    model_config = ConfigDict(populate_by_name=True)

    conversation_id: int = Field(alias='conversationId', description='会话ID')
    title: Optional[str] = Field(default=None, alias='title', description='会话标题')
    model_id: Optional[str] = Field(default=None, alias='modelId', description='模型ID')
    tag_list: Optional[List[str]] = Field(default=None, alias='tagList', description='标签列表')


class DeleteChatConversationModel(BaseModel):
    """
    删除会话模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    conversation_ids: str = Field(description='需要删除的会话ID')


class PinConversationModel(BaseModel):
    """
    置顶会话模型
    """
    model_config = ConfigDict(populate_by_name=True)

    is_pinned: bool = Field(alias='isPinned', description='是否置顶')


class ChatConversationDetailModel(BaseModel):
    """
    会话详情模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    conversation_id: int = Field(description='会话ID')
    title: str = Field(description='会话标题')
    model_id: str = Field(description='模型ID')
    is_pinned: bool = Field(description='是否置顶')
    tag_list: List[str] = Field(default_factory=list, description='标签列表')
    total_tokens: int = Field(description='累计token数')
    message_count: int = Field(description='消息数量')
    messages: List['ChatMessageModel'] = Field(default_factory=list, description='消息列表')
    create_time: datetime = Field(description='创建时间')
    update_time: datetime = Field(description='更新时间')


class ChatConversationTagModel(BaseModel):
    """
    会话标签模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    tag_id: Optional[int] = Field(default=None, description='标签ID')
    tag_name: Optional[str] = Field(default=None, description='标签名称')
    tag_color: Optional[str] = Field(default=None, description='标签颜色')
    user_id: Optional[int] = Field(default=None, description='用户ID')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')
    conversation_count: Optional[int] = Field(default=0, description='关联的会话数量')

    @NotBlank(field_name='tag_name', message='标签名称不能为空')
    @Size(field_name='tag_name', min_length=0, max_length=20, message='标签名称不能超过20个字符')
    def get_tag_name(self):
        return self.tag_name

    def validate_fields(self):
        self.get_tag_name()


class AddChatConversationTagModel(BaseModel):
    """
    新增标签模型
    """
    model_config = ConfigDict(populate_by_name=True)

    tag_name: str = Field(alias='tagName', description='标签名称')
    tag_color: Optional[str] = Field(default=None, alias='tagColor', description='标签颜色')


class DeleteChatConversationTagModel(BaseModel):
    """
    删除标签模型
    """
    model_config = ConfigDict(populate_by_name=True)

    tag_ids: str = Field(alias='tagIds', description='需要删除的标签ID')


class ExportConversationModel(BaseModel):
    """
    导出会话模型
    """
    model_config = ConfigDict(populate_by_name=True)

    download_url: str = Field(alias='downloadUrl', description='下载链接')
    file_name: str = Field(alias='fileName', description='文件名')
    file_size: int = Field(alias='fileSize', description='文件大小')


class ConversationContextModel(BaseModel):
    """
    会话上下文状态模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    total_tokens: int = Field(description='累计使用token数')
    max_tokens: int = Field(description='最大token数')
    usage_percent: int = Field(description='使用百分比')
    message_count: int = Field(description='消息数量')
    warning_level: Literal['normal', 'warning', 'critical'] = Field(description='警告级别')
