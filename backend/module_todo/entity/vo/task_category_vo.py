from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss
from typing import Optional


class TaskCategoryModel(BaseModel):
    """
    任务分类表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    category_id: Optional[int] = Field(default=None, description='分类ID')
    category_name: Optional[str] = Field(default=None, description='分类名称')
    user_id: Optional[int] = Field(default=None, description='用户ID')
    sort_order: Optional[int] = Field(default=None, description='排序顺序')
    create_by: Optional[str] = Field(default=None, description='创建者')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')
    remark: Optional[str] = Field(default=None, description='备注')

    @Xss(field_name='category_name', message='分类名称不能包含脚本字符')
    @NotBlank(field_name='category_name', message='分类名称不能为空')
    @Size(field_name='category_name', min_length=0, max_length=50, message='分类名称不能超过50个字符')
    def get_category_name(self):
        return self.category_name

    def validate_fields(self):
        self.get_category_name()


class TaskCategoryPageQueryModel(BaseModel):
    """
    任务分类管理分页查询模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    category_id: Optional[int] = Field(default=None, description='分类ID')
    category_name: Optional[str] = Field(default=None, description='分类名称')
    user_id: Optional[int] = Field(default=None, description='用户ID')
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
