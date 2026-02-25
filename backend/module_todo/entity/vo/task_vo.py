from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss
from typing import Literal, Optional
from module_todo.annotation.pydantic_annotation import as_query


class TaskModel(BaseModel):
    """
    任务表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    task_id: Optional[int] = Field(default=None, description='任务ID')
    task_title: Optional[str] = Field(default=None, description='任务标题')
    task_content: Optional[str] = Field(default=None, description='任务内容')
    category_id: Optional[int] = Field(default=None, description='分类ID')
    user_id: Optional[int] = Field(default=None, description='用户ID')
    task_type: Optional[Literal['1', '2']] = Field(default=None, description='任务类型（1任务 2待办）')
    status: Optional[Literal['0', '1']] = Field(default=None, description='状态（0待办 1已完成）')
    priority: Optional[Literal['0', '1', '2']] = Field(default=None, description='优先级（0低 1中 2高）')
    due_date: Optional[datetime] = Field(default=None, description='截止日期')
    completed_at: Optional[datetime] = Field(default=None, description='完成时间')
    create_by: Optional[str] = Field(default=None, description='创建者')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')
    remark: Optional[str] = Field(default=None, description='备注')

    @Xss(field_name='task_title', message='任务标题不能包含脚本字符')
    @NotBlank(field_name='task_title', message='任务标题不能为空')
    @Size(field_name='task_title', min_length=0, max_length=200, message='任务标题不能超过200个字符')
    def get_task_title(self):
        return self.task_title

    def validate_fields(self):
        self.get_task_title()


class TaskQueryModel(TaskModel):
    """
    任务管理不分页查询模型
    """
    begin_time: Optional[str] = Field(default=None, description='开始时间')
    end_time: Optional[str] = Field(default=None, description='结束时间')


@as_query
class TaskPageQueryModel(TaskQueryModel):
    """
    任务管理分页查询模型
    """
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class DeleteTaskModel(BaseModel):
    """
    删除任务模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    task_ids: str = Field(description='需要删除的任务ID')


class TaskStatusModel(BaseModel):
    """
    任务状态更新模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    status: Literal['0', '1'] = Field(description='状态（0待办 1已完成）')
