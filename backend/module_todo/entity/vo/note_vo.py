from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss
from typing import Literal, Optional
from module_todo.annotation.pydantic_annotation import as_query


class NoteModel(BaseModel):
    """
    记事表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    note_id: Optional[int] = Field(default=None, description='记事ID')
    note_title: Optional[str] = Field(default=None, description='记事标题')
    note_content: Optional[str] = Field(default=None, description='记事内容')
    category_id: Optional[int] = Field(default=None, description='分类ID')
    user_id: Optional[int] = Field(default=None, description='用户ID')
    status: Optional[Literal['0', '1']] = Field(default=None, description='状态（0正常 1关闭）')
    create_by: Optional[str] = Field(default=None, description='创建者')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')
    remark: Optional[str] = Field(default=None, description='备注')

    @Xss(field_name='note_title', message='记事标题不能包含脚本字符')
    @NotBlank(field_name='note_title', message='记事标题不能为空')
    @Size(field_name='note_title', min_length=0, max_length=200, message='记事标题不能超过200个字符')
    def get_note_title(self):
        return self.note_title

    def validate_fields(self):
        self.get_note_title()


class NoteQueryModel(NoteModel):
    """
    记事管理不分页查询模型
    """
    begin_time: Optional[str] = Field(default=None, description='开始时间')
    end_time: Optional[str] = Field(default=None, description='结束时间')


@as_query
class NotePageQueryModel(NoteQueryModel):
    """
    记事管理分页查询模型
    """
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class DeleteNoteModel(BaseModel):
    """
    删除记事模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    note_ids: str = Field(description='需要删除的记事ID')
