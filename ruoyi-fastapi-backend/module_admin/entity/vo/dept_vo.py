"""
部门模块 VO（View Object / DTO）层

说明（供初学者）：
- 本文件定义部门相关的 Pydantic 模型，用于请求校验、响应结构与服务/控制层之间的数据传输。
- 高级特性：
  1) Pydantic v2：`BaseModel`/`Field` 提供字段声明与校验；`ConfigDict` 配置模型行为。
  2) alias_generator：通过 `to_camel` 自动生成驼峰别名，前后端字段风格一致。
  3) 自定义注解：`NotBlank`、`Size`、`Network(Email)` 用于声明式校验。
  4) `@as_query`：将模型包装为 FastAPI 依赖，自动把 Query 参数解析进模型（高级特性）。

调用链路（这些模型在何处被使用）：
- Controller：作为请求体验证和响应数据（如 `DeptModel`、`DeptQueryModel`、`DeleteDeptModel`）。
- Service：在业务逻辑中用强类型传递数据，对接 DAO/DO 前通过 `model_dump()` 转换。
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field  # Pydantic v2 基础能力
from pydantic.alias_generators import to_camel  # 驼峰别名生成器
from pydantic_validation_decorator import Network, NotBlank, Size  # 自定义字段校验注解
from typing import Literal, Optional
from module_admin.annotation.pydantic_annotation import as_query  # 将模型包装为 Query 依赖


class DeptModel(BaseModel):
    """
    部门表对应pydantic模型
    """

    # alias_generator：下划线 → 驼峰；from_attributes：支持从 ORM 对象构建
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    dept_id: Optional[int] = Field(default=None, description='部门id')
    parent_id: Optional[int] = Field(default=None, description='父部门id')
    ancestors: Optional[str] = Field(default=None, description='祖级列表')
    dept_name: Optional[str] = Field(default=None, description='部门名称')
    order_num: Optional[int] = Field(default=None, description='显示顺序')
    leader: Optional[str] = Field(default=None, description='负责人')
    phone: Optional[str] = Field(default=None, description='联系电话')
    email: Optional[str] = Field(default=None, description='邮箱')
    status: Optional[Literal['0', '1']] = Field(default=None, description='部门状态（0正常 1停用）')
    del_flag: Optional[Literal['0', '2']] = Field(default=None, description='删除标志（0代表存在 2代表删除）')
    create_by: Optional[str] = Field(default=None, description='创建者')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')

    # 部门名称：非空 + 长度约束
    @NotBlank(field_name='dept_name', message='部门名称不能为空')
    @Size(field_name='dept_name', min_length=0, max_length=30, message='部门名称长度不能超过30个字符')
    def get_dept_name(self):
        return self.dept_name

    # 显示顺序：非空
    @NotBlank(field_name='order_num', message='显示顺序不能为空')
    def get_order_num(self):
        return self.order_num

    # 电话：长度上限
    @Size(field_name='phone', min_length=0, max_length=11, message='联系电话长度不能超过11个字符')
    def get_phone(self):
        return self.phone

    # 邮箱：格式 + 长度
    @Network(field_name='email', field_type='EmailStr', message='邮箱格式不正确')
    @Size(field_name='email', min_length=0, max_length=50, message='邮箱长度不能超过50个字符')
    def get_email(self):
        return self.email

    def validate_fields(self):
        # 触发上述四项字段校验
        self.get_dept_name()
        self.get_order_num()
        self.get_phone()
        self.get_email()


@as_query
class DeptQueryModel(DeptModel):
    """
    部门管理不分页查询模型
    """

    begin_time: Optional[str] = Field(default=None, description='开始时间')
    end_time: Optional[str] = Field(default=None, description='结束时间')


class DeleteDeptModel(BaseModel):
    """
    删除部门模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    dept_ids: str = Field(default=None, description='需要删除的部门id')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[str] = Field(default=None, description='更新时间')
