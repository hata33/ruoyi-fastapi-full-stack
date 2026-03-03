"""
聊天模型管理 VO（View Object）

说明：
- 定义模型管理相关的请求/响应模型
- 包括模型列表查询、用户模型配置等
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size
from typing import Literal, Optional


class ChatModelModel(BaseModel):
    """
    聊天模型表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    model_id: Optional[int] = Field(default=None, description='模型ID')
    model_code: Optional[str] = Field(default=None, description='模型代码')
    model_name: Optional[str] = Field(default=None, description='模型名称')
    model_type: Optional[Literal['chat', 'reasoner']] = Field(default=None, description='模型类型')
    max_tokens: Optional[int] = Field(default=None, description='最大token数')
    is_enabled: Optional[bool] = Field(default=None, description='是否启用')
    sort_order: Optional[int] = Field(default=None, description='排序顺序')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')


class ChatModelQueryModel(BaseModel):
    """
    模型查询模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    is_enabled: Optional[bool] = Field(default=None, description='是否启用')


class ChatUserModelConfigModel(BaseModel):
    """
    用户模型配置表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    config_id: Optional[int] = Field(default=None, description='配置ID')
    user_id: Optional[int] = Field(default=None, description='用户ID')
    model_id: Optional[str] = Field(default=None, description='模型ID')
    temperature: Optional[Decimal] = Field(default=None, description='温度参数')
    top_p: Optional[Decimal] = Field(default=None, description='采样参数')
    max_tokens: Optional[int] = Field(default=None, description='最大生成token数')
    preset_name: Optional[Literal['creative', 'balanced', 'precise']] = Field(default=None, description='预设名称')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')

    @NotBlank(field_name='model_id', message='模型ID不能为空')
    def get_model_id(self):
        return self.model_id

    def validate_fields(self):
        self.get_model_id()


class ModelPresetModel(BaseModel):
    """
    模型参数预设模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    preset_name: Literal['creative', 'balanced', 'precise'] = Field(description='预设名称')
    display_name: str = Field(description='显示名称')
    description: str = Field(description='描述')
    temperature: Decimal = Field(description='温度参数')
    top_p: Decimal = Field(description='采样参数')
