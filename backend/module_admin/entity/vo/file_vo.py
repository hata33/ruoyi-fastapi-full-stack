from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Pattern, Size
from typing import Literal, Optional
from module_admin.annotation.pydantic_annotation import as_query


class FileStatus(str, Enum):
    """
    文件状态枚举
    """
    PENDING = "pending"        # 待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"    # 处理完成
    FAILED = "failed"         # 处理失败


class FileModel(BaseModel):
    """
    文件表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    # 主键和基础信息
    file_id: Optional[int] = Field(default=None, description='文件ID')
    original_filename: Optional[str] = Field(default=None, description='原始文件名')
    storage_filename: Optional[str] = Field(default=None, description='存储文件名')
    file_extension: Optional[str] = Field(default=None, description='文件扩展名')
    file_size: Optional[int] = Field(default=None, description='文件大小(字节)')
    file_path: Optional[str] = Field(default=None, description='文件存储路径')

    # 项目相关字段
    project_id: Optional[str] = Field(default=None, description='项目ID')
    project_name: Optional[str] = Field(default=None, description='项目名称')

    # 用户相关字段
    upload_user_id: Optional[int] = Field(default=None, description='上传用户ID')
    upload_username: Optional[str] = Field(default=None, description='上传用户名')

    # 状态和处理信息
    file_status: Optional[FileStatus] = Field(default=FileStatus.PENDING, description='文件状态')
    retry_count: Optional[int] = Field(default=0, description='重试次数')
    error_message: Optional[str] = Field(default=None, description='错误信息')

    # 时间信息
    upload_time: Optional[datetime] = Field(default=None, description='上传时间')
    start_process_time: Optional[datetime] = Field(default=None, description='开始处理时间')
    complete_process_time: Optional[datetime] = Field(default=None, description='完成处理时间')

    # 软删除支持
    is_deleted: Optional[bool] = Field(default=False, description='是否删除')
    delete_time: Optional[datetime] = Field(default=None, description='删除时间')

    # 审计字段
    create_by: Optional[str] = Field(default=None, description='创建者')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')


class FileCreateModel(BaseModel):
    """
    文件创建模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    # 必需字段
    original_filename: str = Field(description='原始文件名')
    storage_filename: str = Field(description='存储文件名')
    file_extension: str = Field(description='文件扩展名')
    file_size: int = Field(description='文件大小(字节)')
    file_path: str = Field(description='文件存储路径')
    project_id: str = Field(description='项目ID')
    upload_user_id: int = Field(description='上传用户ID')

    # 可选字段
    project_name: Optional[str] = Field(default=None, description='项目名称')
    upload_username: Optional[str] = Field(default=None, description='上传用户名')
    create_by: Optional[str] = Field(default=None, description='创建者')

    @NotBlank(field_name='original_filename', message='原始文件名不能为空')
    @Size(field_name='original_filename', min_length=1, max_length=255, message='原始文件名长度不能超过255个字符')
    def get_original_filename(self):
        return self.original_filename

    @NotBlank(field_name='storage_filename', message='存储文件名不能为空')
    @Size(field_name='storage_filename', min_length=1, max_length=255, message='存储文件名长度不能超过255个字符')
    def get_storage_filename(self):
        return self.storage_filename

    @NotBlank(field_name='file_extension', message='文件扩展名不能为空')
    @Size(field_name='file_extension', min_length=1, max_length=10, message='文件扩展名长度不能超过10个字符')
    @Pattern(
        field_name='file_extension',
        regexp='^(txt|md)$',
        message='文件扩展名只支持txt和md格式'
    )
    def get_file_extension(self):
        return self.file_extension

    @NotBlank(field_name='file_path', message='文件存储路径不能为空')
    @Size(field_name='file_path', min_length=1, max_length=500, message='文件存储路径长度不能超过500个字符')
    @Pattern(
        field_name='file_path',
        regexp='^(?!.*\\.\\.).*$',
        message='文件路径不能包含路径遍历字符'
    )
    def get_file_path(self):
        return self.file_path

    @NotBlank(field_name='project_id', message='项目ID不能为空')
    @Size(field_name='project_id', min_length=1, max_length=100, message='项目ID长度不能超过100个字符')
    def get_project_id(self):
        return self.project_id

    def validate_fields(self):
        """验证所有字段"""
        self.get_original_filename()
        self.get_storage_filename()
        self.get_file_extension()
        self.get_file_path()
        self.get_project_id()


class FileUpdateModel(BaseModel):
    """
    文件更新模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    # 可选更新字段
    file_status: Optional[FileStatus] = Field(default=None, description='文件状态')
    retry_count: Optional[int] = Field(default=None, description='重试次数')
    error_message: Optional[str] = Field(default=None, description='错误信息')
    start_process_time: Optional[datetime] = Field(default=None, description='开始处理时间')
    complete_process_time: Optional[datetime] = Field(default=None, description='完成处理时间')
    update_by: Optional[str] = Field(default=None, description='更新者')

    @Size(field_name='error_message', min_length=0, max_length=1000, message='错误信息长度不能超过1000个字符')
    def get_error_message(self):
        return self.error_message


class FileResponseModel(FileModel):
    """
    文件响应模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)


class FileQueryModel(BaseModel):
    """
    文件管理不分页查询模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    # 查询条件
    project_id: Optional[str] = Field(default=None, description='项目ID')
    original_filename: Optional[str] = Field(default=None, description='文件名')
    project_name: Optional[str] = Field(default=None, description='项目名称')
    upload_user_id: Optional[int] = Field(default=None, description='上传用户ID')
    upload_username: Optional[str] = Field(default=None, description='上传用户名')
    file_status: Optional[FileStatus] = Field(default=None, description='文件状态')
    file_extension: Optional[str] = Field(default=None, description='文件扩展名')
    
    # 时间范围查询
    begin_time: Optional[str] = Field(default=None, description='开始时间')
    end_time: Optional[str] = Field(default=None, description='结束时间')
    
    # 软删除状态
    is_deleted: Optional[bool] = Field(default=False, description='是否删除')


@as_query
class FilePageQueryModel(FileQueryModel):
    """
    文件管理分页查询模型
    """

    page_num: int = Field(default=1, ge=1, description='当前页码')
    page_size: int = Field(default=10, ge=1, le=100, description='每页记录数')


class FileStatusUpdateModel(BaseModel):
    """
    文件状态更新模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    file_status: FileStatus = Field(description='文件状态')
    error_message: Optional[str] = Field(default=None, description='错误信息')
    update_by: Optional[str] = Field(default=None, description='更新者')

    @Size(field_name='error_message', min_length=0, max_length=1000, message='错误信息长度不能超过1000个字符')
    def get_error_message(self):
        return self.error_message


class FileDeleteModel(BaseModel):
    """
    文件删除模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    file_ids: str = Field(description='需要删除的文件ID，多个用逗号分隔')
    delete_by: Optional[str] = Field(default=None, description='删除者')


class FileUploadResponseModel(BaseModel):
    """
    文件上传响应模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    file_id: int = Field(description='文件ID')
    original_filename: str = Field(description='原始文件名')
    storage_filename: str = Field(description='存储文件名')
    file_size: int = Field(description='文件大小(字节)')
    file_status: FileStatus = Field(description='文件状态')
    upload_time: datetime = Field(description='上传时间')


class FileProcessProgressModel(BaseModel):
    """
    文件处理进度模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    file_id: int = Field(description='文件ID')
    file_status: FileStatus = Field(description='文件状态')
    # retry_count: int = Field(description='重试次数')
    # error_message: Optional[str] = Field(default=None, description='错误信息')
    start_process_time: Optional[datetime] = Field(default=None, description='开始处理时间')
    complete_process_time: Optional[datetime] = Field(default=None, description='完成处理时间')
    # progress_percentage: Optional[int] = Field(default=None, ge=0, le=100, description='处理进度百分比')
