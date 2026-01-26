"""
定时任务控制器模块

本模块处理系统定时任务的所有 HTTP 请求，包括：
- 定时任务的增删改查（CRUD）操作
- 定时任务状态修改（启用/停用）
- 定时任务立即执行
- 定时任务日志查询和管理
- 定时任务导出

主要依赖：
- FastAPI: Web 框架，处理路由和请求
- APScheduler: 定时任务调度框架
- SQLAlchemy: 数据库 ORM

作者: RuoYi Team
"""

from datetime import datetime

# FastAPI 核心组件
from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic_validation_decorator import ValidateFields

# 配置相关
from config.enums import BusinessType
from config.get_db import get_db

# AOP 切面：权限控制、日志记录
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth

# 数据模型（VO）
from module_admin.entity.vo.job_vo import (
    DeleteJobLogModel,
    DeleteJobModel,
    EditJobModel,
    JobLogPageQueryModel,
    JobModel,
    JobPageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel

# 业务服务层
from module_admin.service.job_log_service import JobLogService
from module_admin.service.job_service import JobService
from module_admin.service.login_service import LoginService

# 工具类
from utils.common_util import bytes2file_response
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


# ==================== 路由配置 ====================
# 创建定时任务路由器
# prefix: 所有接口的路径前缀为 /monitor
# dependencies: 全局依赖，所有接口都需要先验证用户登录状态
jobController = APIRouter(prefix='/monitor', dependencies=[Depends(LoginService.get_current_user)])


# ==================== 定时任务查询接口 ====================

@jobController.get(
    '/job/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:list'))]
)
async def get_system_job_list(
    request: Request,
    job_page_query: JobPageQueryModel = Depends(JobPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
):
    """
    获取定时任务列表（分页）

    根据查询条件获取定时任务列表，支持分页、排序、搜索等功能。

    权限: monitor:job:list

    参数:
        job_page_query: 分页查询参数（页码、每页数量、搜索条件等）

    返回:
        PageResponseModel: 分页结果，包含定时任务列表和分页信息
    """
    # 调用服务层获取分页数据
    notice_page_query_result = await JobService.get_job_list_services(query_db, job_page_query, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=notice_page_query_result)


@jobController.get(
    '/job/{job_id}', response_model=JobModel, dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:query'))]
)
async def query_detail_system_job(request: Request, job_id: int, query_db: AsyncSession = Depends(get_db)):
    """
    获取定时任务详细信息

    查询指定定时任务的详细资料，用于编辑时回显数据。

    权限: monitor:job:query

    参数:
        job_id: 定时任务 ID

    返回:
        JobModel: 定时任务详细信息
    """
    job_detail_result = await JobService.job_detail_services(query_db, job_id)
    logger.info(f'获取job_id为{job_id}的信息成功')

    return ResponseUtil.success(data=job_detail_result)


# ==================== 定时任务增删改接口 ====================

@jobController.post('/job', dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:add'))])
@ValidateFields(validate_model='add_job')
@Log(title='定时任务', business_type=BusinessType.INSERT)
async def add_system_job(
    request: Request,
    add_job: JobModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    添加定时任务

    创建一个新的定时任务。
    支持的调度类型：Cron 表达式、固定间隔等。

    权限: monitor:job:add
    日志: 记录定时任务添加操作

    参数:
        add_job: 定时任务信息（任务名称、调度类型、Cron 表达式、调用目标等）

    返回:
        dict: 操作结果消息
    """
    # 记录创建人和创建时间
    add_job.create_by = current_user.user.user_name
    add_job.create_time = datetime.now()
    add_job.update_by = current_user.user.user_name
    add_job.update_time = datetime.now()
    add_job_result = await JobService.add_job_services(query_db, add_job)
    logger.info(add_job_result.message)

    return ResponseUtil.success(msg=add_job_result.message)


@jobController.put('/job', dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:edit'))])
@ValidateFields(validate_model='edit_job')
@Log(title='定时任务', business_type=BusinessType.UPDATE)
async def edit_system_job(
    request: Request,
    edit_job: EditJobModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    编辑定时任务

    更新现有的定时任务信息。

    权限: monitor:job:edit
    日志: 记录定时任务编辑操作

    参数:
        edit_job: 要更新的定时任务信息

    返回:
        dict: 操作结果消息
    """
    # 记录修改人和修改时间
    edit_job.update_by = current_user.user.user_name
    edit_job.update_time = datetime.now()
    edit_job_result = await JobService.edit_job_services(query_db, edit_job)
    logger.info(edit_job_result.message)

    return ResponseUtil.success(msg=edit_job_result.message)


@jobController.delete('/job/{job_ids}', dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:remove'))])
@Log(title='定时任务', business_type=BusinessType.DELETE)
async def delete_system_job(request: Request, job_ids: str, query_db: AsyncSession = Depends(get_db)):
    """
    删除定时任务

    批量删除定时任务，支持一次删除多个任务（用逗号分隔 ID）。

    权限: monitor:job:remove
    日志: 记录定时任务删除操作

    参数:
        job_ids: 要删除的定时任务 ID 列表，逗号分隔（如 "1,2,3"）

    返回:
        dict: 操作结果消息
    """
    delete_job = DeleteJobModel(jobIds=job_ids)
    delete_job_result = await JobService.delete_job_services(query_db, delete_job)
    logger.info(delete_job_result.message)

    return ResponseUtil.success(msg=delete_job_result.message)


# ==================== 定时任务控制接口 ====================

@jobController.put('/job/changeStatus', dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:changeStatus'))])
@Log(title='定时任务', business_type=BusinessType.UPDATE)
async def change_system_job_status(
    request: Request,
    change_job: EditJobModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    修改定时任务状态

    启用或停用定时任务。
    停用的任务不会被执行，但不会删除。

    权限: monitor:job:changeStatus
    日志: 记录状态修改操作

    参数:
        change_job: 包含任务 ID 和新状态（0=正常, 1=停用）

    返回:
        dict: 操作结果消息
    """
    # 构造状态更新对象
    # type='status' 表示只更新状态字段
    edit_job = EditJobModel(
        jobId=change_job.job_id,
        status=change_job.status,
        updateBy=current_user.user.user_name,
        updateTime=datetime.now(),
        type='status',
    )
    edit_job_result = await JobService.edit_job_services(query_db, edit_job)
    logger.info(edit_job_result.message)

    return ResponseUtil.success(msg=edit_job_result.message)


@jobController.put('/job/run', dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:changeStatus'))])
@Log(title='定时任务', business_type=BusinessType.UPDATE)
async def execute_system_job(request: Request, execute_job: JobModel, query_db: AsyncSession = Depends(get_db)):
    """
    立即执行定时任务

    立即执行指定的定时任务一次，不影响正常的调度计划。

    权限: monitor:job:changeStatus
    日志: 记录任务执行操作

    参数:
        execute_job: 要执行的定时任务信息

    返回:
        dict: 操作结果消息
    """
    execute_job_result = await JobService.execute_job_once_services(query_db, execute_job)
    logger.info(execute_job_result.message)

    return ResponseUtil.success(msg=execute_job_result.message)


# ==================== 定时任务导出接口 ====================

@jobController.post('/job/export', dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:export'))])
@Log(title='定时任务', business_type=BusinessType.EXPORT)
async def export_system_job_list(
    request: Request,
    job_page_query: JobPageQueryModel = Form(),
    query_db: AsyncSession = Depends(get_db),
):
    """
    导出定时任务列表

    根据查询条件导出定时任务数据到 Excel 文件。

    权限: monitor:job:export
    日志: 记录导出操作

    参数:
        job_page_query: 查询条件（筛选要导出的定时任务）

    返回:
        StreamingResponse: Excel 文件流
    """
    # 获取全量数据（不分页）
    job_query_result = await JobService.get_job_list_services(query_db, job_page_query, is_page=False)
    job_export_result = await JobService.export_job_list_services(request, job_query_result)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(job_export_result))


# ==================== 定时任务日志查询接口 ====================

@jobController.get(
    '/jobLog/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:list'))]
)
async def get_system_job_log_list(
    request: Request,
    job_log_page_query: JobLogPageQueryModel = Depends(JobLogPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
):
    """
    获取定时任务执行日志列表（分页）

    根据查询条件获取定时任务执行日志列表，支持分页、排序、搜索等功能。

    权限: monitor:job:list

    参数:
        job_log_page_query: 分页查询参数（页码、每页数量、搜索条件等）

    返回:
        PageResponseModel: 分页结果，包含定时任务日志列表和分页信息
    """
    # 调用服务层获取分页数据
    job_log_page_query_result = await JobLogService.get_job_log_list_services(
        query_db, job_log_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=job_log_page_query_result)


# ==================== 定时任务日志管理接口 ====================

@jobController.delete('/jobLog/clean', dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:remove'))])
@Log(title='定时任务调度日志', business_type=BusinessType.CLEAN)
async def clear_system_job_log(request: Request, query_db: AsyncSession = Depends(get_db)):
    """
    清空定时任务日志

    清空所有定时任务的执行日志。

    权限: monitor:job:remove
    日志: 记录日志清空操作

    返回:
        dict: 操作结果消息
    """
    clear_job_log_result = await JobLogService.clear_job_log_services(query_db)
    logger.info(clear_job_log_result.message)

    return ResponseUtil.success(msg=clear_job_log_result.message)


@jobController.delete('/jobLog/{job_log_ids}', dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:remove'))])
@Log(title='定时任务调度日志', business_type=BusinessType.DELETE)
async def delete_system_job_log(request: Request, job_log_ids: str, query_db: AsyncSession = Depends(get_db)):
    """
    删除定时任务日志

    批量删除定时任务执行日志，支持一次删除多条日志（用逗号分隔 ID）。

    权限: monitor:job:remove
    日志: 记录日志删除操作

    参数:
        job_log_ids: 要删除的日志 ID 列表，逗号分隔（如 "1,2,3"）

    返回:
        dict: 操作结果消息
    """
    delete_job_log = DeleteJobLogModel(jobLogIds=job_log_ids)
    delete_job_log_result = await JobLogService.delete_job_log_services(query_db, delete_job_log)
    logger.info(delete_job_log_result.message)

    return ResponseUtil.success(msg=delete_job_log_result.message)


@jobController.post('/jobLog/export', dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:export'))])
@Log(title='定时任务调度日志', business_type=BusinessType.EXPORT)
async def export_system_job_log_list(
    request: Request,
    job_log_page_query: JobLogPageQueryModel = Form(),
    query_db: AsyncSession = Depends(get_db),
):
    """
    导出定时任务日志列表

    根据查询条件导出定时任务执行日志数据到 Excel 文件。

    权限: monitor:job:export
    日志: 记录导出操作

    参数:
        job_log_page_query: 查询条件（筛选要导出的日志）

    返回:
        StreamingResponse: Excel 文件流
    """
    # 获取全量数据（不分页）
    job_log_query_result = await JobLogService.get_job_log_list_services(query_db, job_log_page_query, is_page=False)
    job_log_export_result = await JobLogService.export_job_log_list_services(request, job_log_query_result)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(job_log_export_result))
