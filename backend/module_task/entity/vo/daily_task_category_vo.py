from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class DailyTaskCategoryModel(BaseModel):
    """
    每日任务分类表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    category_id: Optional[int] = Field(default=None, description='分类ID')
    category_name: Optional[str] = Field(default=None, description='分类名称')
    category_icon: Optional[str] = Field(default=None, description='分类图标')
    sort_order: Optional[int] = Field(default=None, description='排序顺序')
    user_id: Optional[int] = Field(default=None, description='用户ID')
    create_by: Optional[str] = Field(default=None, description='创建者')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')

    @Xss(field_name='category_name', message='分类名称不能包含脚本字符')
    @NotBlank(field_name='category_name', message='分类名称不能为空')
    @Size(field_name='category_name', min_length=0, max_length=50, message='分类名称不能超过50个字符')
    def get_category_name(self):
        return self.category_name

    @Size(field_name='category_icon', min_length=0, max_length=50, message='分类图标不能超过50个字符')
    def get_category_icon(self):
        return self.category_icon

    def validate_fields(self):
        self.get_category_name()
        self.get_category_icon()


class DailyTaskCategoryQueryModel(BaseModel):
    """
    每日任务分类管理不分页查询模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    category_id: Optional[int] = Field(default=None, description='分类ID')
    category_name: Optional[str] = Field(default=None, description='分类名称')
    category_icon: Optional[str] = Field(default=None, description='分类图标')
    sort_order: Optional[int] = Field(default=None, description='排序顺序')
    user_id: Optional[int] = Field(default=None, description='用户ID')
    create_by: Optional[str] = Field(default=None, description='创建者')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')
    begin_time: Optional[str] = Field(default=None, description='开始时间')
    end_time: Optional[str] = Field(default=None, description='结束时间')


class DailyTaskCategoryPageQueryModel(DailyTaskCategoryQueryModel):
    """
    每日任务分类管理分页查询模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class DeleteDailyTaskCategoryModel(BaseModel):
    """
    删除每日任务分类模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    category_ids: str = Field(description='需要删除的分类ID')


class DailyTaskCategoryReorderModel(BaseModel):
    """
    每日任务分类批量排序模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    categories: list[dict] = Field(description='分类列表，包含category_id和sort_order')
