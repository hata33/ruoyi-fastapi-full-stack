from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class DailyTaskModel(BaseModel):
    """
    每日任务表对应pydantic模型
    """
    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True
    )

    task_id: Optional[int] = Field(default=None, description='任务ID')
    title: Optional[str] = Field(default=None, description='任务标题')
    description: Optional[str] = Field(default=None, description='任务描述')
    task_type: Optional[Literal['daily', 'once', 'long']] = Field(
        default=None, description='任务类型（daily每日任务 once一次性任务 long长期任务）'
    )
    status: Optional[Literal['pending', 'completed', 'disabled']] = Field(
        default=None, description='状态（pending待完成 completed已完成 disabled已禁用）'
    )
    is_pinned: Optional[bool] = Field(default=None, description='是否置顶')
    sort_order: Optional[int] = Field(default=None, description='排序顺序')
    completion_count: Optional[int] = Field(default=None, description='累计完成次数')
    icon_type: Optional[str] = Field(default=None, description='图标类型')
    user_id: Optional[int] = Field(default=None, description='用户ID')
    category_id: Optional[int] = Field(default=None, description='分类ID')
    last_completed_at: Optional[datetime] = Field(default=None, description='最后完成时间')
    disabled_at: Optional[datetime] = Field(default=None, description='禁用时间')
    create_by: Optional[str] = Field(default=None, description='创建者')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')
    remark: Optional[str] = Field(default=None, description='备注')

    @Xss(field_name='title', message='任务标题不能包含脚本字符')
    @NotBlank(field_name='title', message='任务标题不能为空')
    @Size(field_name='title', min_length=0, max_length=200, message='任务标题不能超过200个字符')
    def get_title(self):
        return self.title

    @Size(field_name='description', min_length=0, max_length=2000, message='任务描述不能超过2000个字符')
    def get_description(self):
        return self.description

    def validate_fields(self):
        self.get_title()
        self.get_description()


class DailyTaskQueryModel(BaseModel):
    """
    每日任务管理不分页查询模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    task_id: Optional[int] = Field(default=None, description='任务ID')
    title: Optional[str] = Field(default=None, description='任务标题')
    description: Optional[str] = Field(default=None, description='任务描述')
    task_type: Optional[Literal['daily', 'once', 'long']] = Field(
        default=None, description='任务类型（daily每日任务 once一次性任务 long长期任务）'
    )
    status: Optional[Literal['pending', 'completed', 'disabled']] = Field(
        default=None, description='状态（pending待完成 completed已完成 disabled已禁用）'
    )
    is_pinned: Optional[bool] = Field(default=None, description='是否置顶')
    sort_order: Optional[int] = Field(default=None, description='排序顺序')
    completion_count: Optional[int] = Field(default=None, description='累计完成次数')
    icon_type: Optional[str] = Field(default=None, description='图标类型')
    user_id: Optional[int] = Field(default=None, description='用户ID')
    category_id: Optional[int] = Field(default=None, description='分类ID')
    last_completed_at: Optional[datetime] = Field(default=None, description='最后完成时间')
    disabled_at: Optional[datetime] = Field(default=None, description='禁用时间')
    create_by: Optional[str] = Field(default=None, description='创建者')
    remark: Optional[str] = Field(default=None, description='备注')
    begin_time: Optional[str] = Field(default=None, description='开始时间')
    end_time: Optional[str] = Field(default=None, description='结束时间')


class DailyTaskPageQueryModel(DailyTaskQueryModel):
    """
    每日任务管理分页查询模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class DeleteDailyTaskModel(BaseModel):
    """
    删除每日任务模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    task_ids: str = Field(description='需要删除的任务ID')


class DailyTaskStatusModel(BaseModel):
    """
    每日任务状态更新模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    status: Literal['pending', 'completed', 'disabled'] = Field(
        description='状态（pending待完成 completed已完成 disabled已禁用）'
    )


class DailyTaskCompleteModel(BaseModel):
    """
    每日任务完成模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    task_id: int = Field(description='任务ID')


class DailyTaskPinModel(BaseModel):
    """
    每日任务置顶模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    is_pinned: bool = Field(description='是否置顶')


class DailyTaskReorderModel(BaseModel):
    """
    每日任务批量排序模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    tasks: list[dict] = Field(description='任务列表，包含task_id和sort_order')
