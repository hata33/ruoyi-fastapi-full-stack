"""
部门管理-控制层（Controller）

说明（供初学者）：
- 本文件定义部门相关的 HTTP 接口，使用 FastAPI 的路由与依赖注入。
- 高级特性：
  1) Depends：依赖注入（自动注入 DB 会话、登录用户、数据权限 SQL 等）。
  2) @ValidateFields：基于 Pydantic 的参数校验装饰器。
  3) @Log：自定义注解（AOP），自动记录操作日志。
  4) 全异步：async/await 提升并发能力。

调用链路（从接口到数据库）：
- 获取可选父级部门：Controller.get_system_dept_tree_for_edit_option → DeptService.get_dept_for_edit_option_services → DeptDao.get_dept_info_for_edit_option
- 部门列表：Controller.get_system_dept_list → DeptService.get_dept_list_services → DeptDao.get_dept_list
- 新增部门：Controller.add_system_dept → DeptService.add_dept_services → DeptDao.add_dept_dao
- 编辑部门：Controller.edit_system_dept → DeptService.edit_dept_services → DeptDao.edit_dept_dao / update_dept_children_dao 等
- 删除部门：Controller.delete_system_dept → DeptService.delete_dept_services → DeptDao.delete_dept_dao
- 详情：Controller.query_detail_system_dept → DeptService.dept_detail_services → DeptDao.get_dept_detail_by_id
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Request  # 路由与依赖注入
from pydantic_validation_decorator import ValidateFields  # 参数校验装饰器
from sqlalchemy.ext.asyncio import AsyncSession  # 异步数据库会话
from typing import List
from config.enums import BusinessType  # 日志业务类型
from config.get_db import get_db  # 依赖：获取 DB 会话
from module_admin.annotation.log_annotation import Log  # AOP 日志注解
from module_admin.aspect.data_scope import GetDataScope  # 依赖：数据权限 SQL
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth  # 接口权限校验
from module_admin.entity.vo.dept_vo import DeleteDeptModel, DeptModel, DeptQueryModel  # 部门 VO
from module_admin.entity.vo.user_vo import CurrentUserModel  # 当前用户 VO
from module_admin.service.dept_service import DeptService  # 部门服务层
from module_admin.service.login_service import LoginService  # 登录服务（获取当前用户）
from utils.log_util import logger  # 日志
from utils.response_util import ResponseUtil  # 统一响应


# 部门路由分组：所有接口默认要求登录
deptController = APIRouter(prefix='/system/dept', dependencies=[Depends(LoginService.get_current_user)])


# 说明：获取“编辑用”的可选父级部门列表（排除自身及后代），带数据权限
@deptController.get(
    '/list/exclude/{dept_id}',
    response_model=List[DeptModel],
    dependencies=[Depends(CheckUserInterfaceAuth('system:dept:list'))],
)
async def get_system_dept_tree_for_edit_option(
    request: Request,  # 请求对象
    dept_id: int,  # 路径参数：部门ID（将被排除）
    query_db: AsyncSession = Depends(get_db),  # DB 会话
    data_scope_sql: str = Depends(GetDataScope('SysDept')),  # 数据权限 SQL
):
    # 组装查询条件对象
    dept_query = DeptModel(deptId=dept_id)
    # 调用服务层返回可作为父级的部门列表
    dept_query_result = await DeptService.get_dept_for_edit_option_services(query_db, dept_query, data_scope_sql)
    logger.info('获取成功')

    return ResponseUtil.success(data=dept_query_result)


# 说明：按条件查询部门列表（不分页），带数据权限
@deptController.get(
    '/list', response_model=List[DeptModel], dependencies=[Depends(CheckUserInterfaceAuth('system:dept:list'))]
)
async def get_system_dept_list(
    request: Request,  # 请求对象
    dept_query: DeptQueryModel = Depends(DeptQueryModel.as_query),  # 查询条件模型
    query_db: AsyncSession = Depends(get_db),  # DB 会话
    data_scope_sql: str = Depends(GetDataScope('SysDept')),  # 数据权限 SQL
):
    # 调用服务层获取列表
    dept_query_result = await DeptService.get_dept_list_services(query_db, dept_query, data_scope_sql)
    logger.info('获取成功')

    return ResponseUtil.success(data=dept_query_result)


# 说明：新增部门
@deptController.post('', dependencies=[Depends(CheckUserInterfaceAuth('system:dept:add'))])
@ValidateFields(validate_model='add_dept')  # 参数校验：add_dept 模型
@Log(title='部门管理', business_type=BusinessType.INSERT)  # AOP 日志：新增
async def add_system_dept(
    request: Request,  # 请求对象
    add_dept: DeptModel,  # 请求体：新增部门数据
    query_db: AsyncSession = Depends(get_db),  # DB 会话
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),  # 当前用户
):
    # 设置审计字段
    add_dept.create_by = current_user.user.user_name
    add_dept.create_time = datetime.now()
    add_dept.update_by = current_user.user.user_name
    add_dept.update_time = datetime.now()
    # 服务层：业务校验 + 入库
    add_dept_result = await DeptService.add_dept_services(query_db, add_dept)
    logger.info(add_dept_result.message)

    return ResponseUtil.success(data=add_dept_result)


# 说明：编辑部门
@deptController.put('', dependencies=[Depends(CheckUserInterfaceAuth('system:dept:edit'))])
@ValidateFields(validate_model='edit_dept')  # 参数校验：edit_dept 模型
@Log(title='部门管理', business_type=BusinessType.UPDATE)  # AOP 日志：更新
async def edit_system_dept(
    request: Request,  # 请求对象
    edit_dept: DeptModel,  # 请求体：编辑部门数据
    query_db: AsyncSession = Depends(get_db),  # DB 会话
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),  # 当前用户
    data_scope_sql: str = Depends(GetDataScope('SysDept')),  # 数据权限 SQL
):
    # 非管理员需要先做数据权限校验
    if not current_user.user.admin:
        await DeptService.check_dept_data_scope_services(query_db, edit_dept.dept_id, data_scope_sql)
    # 审计字段
    edit_dept.update_by = current_user.user.user_name
    edit_dept.update_time = datetime.now()
    # 服务层：执行业务校验与更新
    edit_dept_result = await DeptService.edit_dept_services(query_db, edit_dept)
    logger.info(edit_dept_result.message)

    return ResponseUtil.success(msg=edit_dept_result.message)


# 说明：批量删除部门（逻辑删除），逐个做数据权限校验
@deptController.delete('/{dept_ids}', dependencies=[Depends(CheckUserInterfaceAuth('system:dept:remove'))])
@Log(title='部门管理', business_type=BusinessType.DELETE)
async def delete_system_dept(
    request: Request,  # 请求对象
    dept_ids: str,  # 路径参数：逗号分隔部门ID
    query_db: AsyncSession = Depends(get_db),  # DB 会话
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),  # 当前用户
    data_scope_sql: str = Depends(GetDataScope('SysDept')),  # 数据权限 SQL
):
    # 解析 ID 列表并逐个校验权限
    dept_id_list = dept_ids.split(',') if dept_ids else []
    if dept_id_list:
        for dept_id in dept_id_list:
            if not current_user.user.admin:
                await DeptService.check_dept_data_scope_services(query_db, int(dept_id), data_scope_sql)
    # 组装删除对象与审计字段
    delete_dept = DeleteDeptModel(deptIds=dept_ids)
    delete_dept.update_by = current_user.user.user_name
    delete_dept.update_time = datetime.now()
    delete_dept_result = await DeptService.delete_dept_services(query_db, delete_dept)
    logger.info(delete_dept_result.message)

    return ResponseUtil.success(msg=delete_dept_result.message)


# 说明：查询部门详情（非管理员需校验数据权限）
@deptController.get(
    '/{dept_id}', response_model=DeptModel, dependencies=[Depends(CheckUserInterfaceAuth('system:dept:query'))]
)
async def query_detail_system_dept(
    request: Request,  # 请求对象
    dept_id: int,  # 路径参数：部门ID
    query_db: AsyncSession = Depends(get_db),  # DB 会话
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),  # 当前用户
    data_scope_sql: str = Depends(GetDataScope('SysDept')),  # 数据权限 SQL
):
    if not current_user.user.admin:
        await DeptService.check_dept_data_scope_services(query_db, dept_id, data_scope_sql)
    detail_dept_result = await DeptService.dept_detail_services(query_db, dept_id)
    logger.info(f'获取dept_id为{dept_id}的信息成功')

    return ResponseUtil.success(data=detail_dept_result)
