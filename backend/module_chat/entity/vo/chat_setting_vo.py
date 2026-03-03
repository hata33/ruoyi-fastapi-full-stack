"""
用户设置 VO（View Object）

说明：
- 定义用户设置相关的请求/响应模型
- 包括主题、默认模型、流式输出等配置
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import Size
from typing import Literal, Optional


class ChatUserSettingModel(BaseModel):
    """
    用户设置表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    setting_id: Optional[int] = Field(default=None, description='设置ID')
    user_id: Optional[int] = Field(default=None, description='用户ID')
    theme_mode: Optional[Literal['light', 'dark', 'system']] = Field(default=None, description='主题模式')
    default_model: Optional[str] = Field(default=None, description='默认模型')
    enable_search: Optional[bool] = Field(default=None, description='是否启用联网搜索')
    stream_output: Optional[bool] = Field(default=None, description='是否启用流式输出')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')


class UpdateChatUserSettingModel(BaseModel):
    """
    更新用户设置模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    theme_mode: Optional[Literal['light', 'dark', 'system']] = Field(default=None, description='主题模式')
    default_model: Optional[str] = Field(default=None, description='默认模型')
    enable_search: Optional[bool] = Field(default=None, description='是否启用联网搜索')
    stream_output: Optional[bool] = Field(default=None, description='是否启用流式输出')
    font_size: Optional[int] = Field(default=None, description='字体大小')

    @Size(field_name='font_size', min_value=12, max_value=20, message='字体大小必须在12-20之间')
    def get_font_size(self):
        return self.font_size

    def validate_fields(self):
        if self.font_size is not None:
            self.get_font_size()


class ChatUserSettingDetailModel(BaseModel):
    """
    用户设置详情模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    theme_mode: Literal['light', 'dark', 'system'] = Field(description='主题模式')
    default_model: Optional[str] = Field(default=None, description='默认模型')
    enable_search: bool = Field(description='是否启用联网搜索')
    stream_output: bool = Field(description='是否启用流式输出')
    font_size: Optional[int] = Field(default=14, description='字体大小')
    language: Optional[str] = Field(default='zh-CN', description='语言设置')
