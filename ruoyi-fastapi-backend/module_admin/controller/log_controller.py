"""
系统日志控制器模块

本模块处理系统日志监控的所有 HTTP 请求，包括：
- 操作日志的查询、删除、清空、导出
- 登录日志的查询、删除、清空、导出
- 账户解锁功能

主要依赖：
- FastAPI: Web 框架，处理路由和请求
- SQLAlchemy: 数据库 ORM

作者: RuoYi Team
"""

# FastAPI 核心组件
from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession

# 配置相关
from config.enums import BusinessType
from config.get_db import get_db

# AOP 切面：权限控制、日志记录
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth

# 数据模型（VO）
from module_admin.entity.vo.log_vo import (
    DeleteLoginLogModel,
    DeleteOperLogModel,
    LoginLogPageQueryModel,
    OperLogPageQueryModel,
    UnlockUser,
)

# 业务服务层
from module_admin.service.log_service import LoginLogService, OperationLogService
from module_admin.service.login_service import LoginService

# 工具类
from utils.common_util import bytes2file_response
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


# ==================== 路由配置 ====================
# 创建系统日志路由器
# prefix: 所有接口的路径前缀为 /monitor
# dependencies: 全局依赖，所有接口都需要先验证用户登录状态
logController = APIRouter(prefix='/monitor', dependencies=[Depends(LoginService.get_current_user)])


# ==================== 操作日志接口 ====================

@logController.get(
    '/operlog/list',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('monitor:operlog:list'))],
)
async def get_system_operation_log_list(
    request: Request,
    operation_log_page_query: OperLogPageQueryModel = Depends(OperLogPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
):
    """
    获取操作日志列表（分页）

    根据查询条件获取操作日志列表，支持分页、排序、搜索等功能。
    操作日志记录用户在系统中的各种操作（增删改查等）。

    权限: monitor:operlog:list

    参数:
        operation_log_page_query: 分页查询参数（页码、每页数量、搜索条件等）

    返回:
        PageResponseModel: 分页结果，包含操作日志列表和分页信息
    """
    # 调用服务层获取分页数据
    operation_log_page_query_result = await OperationLogService.get_operation_log_list_services(
        query_db, operation_log_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=operation_log_page_query_result)


@logController.delete('/operlog/clean', dependencies=[Depends(CheckUserInterfaceAuth('monitor:operlog:remove'))])
@Log(title='操作日志', business_type=BusinessType.CLEAN)
async def clear_system_operation_log(request: Request, query_db: AsyncSession = Depends(get_db)):
    """
    清空操作日志

    清空所有的操作日志记录。

    权限: monitor:operlog:remove
    日志: 记录日志清空操作

    返回:
        dict: 操作结果消息
    """
    clear_operation_log_result = await OperationLogService.clear_operation_log_services(query_db)
    logger.info(clear_operation_log_result.message)

    return ResponseUtil.success(msg=clear_operation_log_result.message)


@logController.delete('/operlog/{oper_ids}', dependencies=[Depends(CheckUserInterfaceAuth('monitor:operlog:remove'))])
@Log(title='操作日志', business_type=BusinessType.DELETE)
async def delete_system_operation_log(request: Request, oper_ids: str, query_db: AsyncSession = Depends(get_db)):
    """
    删除操作日志

    批量删除操作日志，支持一次删除多条日志（用逗号分隔 ID）。

    权限: monitor:operlog:remove
    日志: 记录日志删除操作

    参数:
        oper_ids: 要删除的日志 ID 列表，逗号分隔（如 "1,2,3"）

    返回:
        dict: 操作结果消息
    """
    delete_operation_log = DeleteOperLogModel(operIds=oper_ids)
    delete_operation_log_result = await OperationLogService.delete_operation_log_services(
        query_db, delete_operation_log
    )
    logger.info(delete_operation_log_result.message)

    return ResponseUtil.success(msg=delete_operation_log_result.message)


@logController.post('/operlog/export', dependencies=[Depends(CheckUserInterfaceAuth('monitor:operlog:export'))])
@Log(title='操作日志', business_type=BusinessType.EXPORT)
async def export_system_operation_log_list(
    request: Request,
    operation_log_page_query: OperLogPageQueryModel = Form(),
    query_db: AsyncSession = Depends(get_db),
):
    """
    导出操作日志列表

    根据查询条件导出操作日志数据到 Excel 文件。

    权限: monitor:operlog:export
    日志: 记录导出操作

    参数:
        operation_log_page_query: 查询条件（筛选要导出的日志）

    返回:
        StreamingResponse: Excel 文件流
    """
    # 获取全量数据（不分页）
    operation_log_query_result = await OperationLogService.get_operation_log_list_services(
        query_db, operation_log_page_query, is_page=False
    )
    operation_log_export_result = await OperationLogService.export_operation_log_list_services(
        request, operation_log_query_result
    )
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(operation_log_export_result))


# ==================== 登录日志接口 ====================

@logController.get(
    '/logininfor/list',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('monitor:logininfor:list'))],
)
async def get_system_login_log_list(
    request: Request,
    login_log_page_query: LoginLogPageQueryModel = Depends(LoginLogPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
):
    """
    获取登录日志列表（分页）

    根据查询条件获取登录日志列表，支持分页、排序、搜索等功能。
    登录日志记录用户的登录、登出操作。

    权限: monitor:logininfor:list

    参数:
        login_log_page_query: 分页查询参数（页码、每页数量、搜索条件等）

    返回:
        PageResponseModel: 分页结果，包含登录日志列表和分页信息
    """
    # 调用服务层获取分页数据
    login_log_page_query_result = await LoginLogService.get_login_log_list_services(
        query_db, login_log_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=login_log_page_query_result)


@logController.delete('/logininfor/clean', dependencies=[Depends(CheckUserInterfaceAuth('monitor:logininfor:remove'))])
@Log(title='登录日志', business_type=BusinessType.CLEAN)
async def clear_system_login_log(request: Request, query_db: AsyncSession = Depends(get_db)):
    """
    清空登录日志

    清空所有的登录日志记录。

    权限: monitor:logininfor:remove
    日志: 记录日志清空操作

    返回:
        dict: 操作结果消息
    """
    clear_login_log_result = await LoginLogService.clear_login_log_services(query_db)
    logger.info(clear_login_log_result.message)

    return ResponseUtil.success(msg=clear_login_log_result.message)


@logController.delete(
    '/logininfor/{info_ids}', dependencies=[Depends(CheckUserInterfaceAuth('monitor:logininfor:remove'))]
)
@Log(title='登录日志', business_type=BusinessType.DELETE)
async def delete_system_login_log(request: Request, info_ids: str, query_db: AsyncSession = Depends(get_db)):
    """
    删除登录日志

    批量删除登录日志，支持一次删除多条日志（用逗号分隔 ID）。

    权限: monitor:logininfor:remove
    日志: 记录日志删除操作

    参数:
        info_ids: 要删除的日志 ID 列表，逗号分隔（如 "1,2,3"）

    返回:
        dict: 操作结果消息
    """
    delete_login_log = DeleteLoginLogModel(infoIds=info_ids)
    delete_login_log_result = await LoginLogService.delete_login_log_services(query_db, delete_login_log)
    logger.info(delete_login_log_result.message)

    return ResponseUtil.success(msg=delete_login_log_result.message)


@logController.get(
    '/logininfor/unlock/{user_name}', dependencies=[Depends(CheckUserInterfaceAuth('monitor:logininfor:unlock'))]
)
@Log(title='账户解锁', business_type=BusinessType.OTHER)
async def unlock_system_user(request: Request, user_name: str, query_db: AsyncSession = Depends(get_db)):
    """
    解锁用户账户

    解锁被锁定的用户账户。
    用户因多次登录失败会被自动锁定，管理员可以手动解锁。

    权限: monitor:logininfor:unlock
    日志: 记录账户解锁操作

    参数:
        user_name: 要解锁的用户名

    返回:
        dict: 操作结果消息
    """
    unlock_user = UnlockUser(userName=user_name)
    unlock_user_result = await LoginLogService.unlock_user_services(request, unlock_user)
    logger.info(unlock_user_result.message)

    return ResponseUtil.success(msg=unlock_user_result.message)


@logController.post('/logininfor/export', dependencies=[Depends(CheckUserInterfaceAuth('monitor:logininfor:export'))])
@Log(title='登录日志', business_type=BusinessType.EXPORT)
async def export_system_login_log_list(
    request: Request,
    login_log_page_query: LoginLogPageQueryModel = Form(),
    query_db: AsyncSession = Depends(get_db),
):
    """
    导出登录日志列表

    根据查询条件导出登录日志数据到 Excel 文件。

    权限: monitor:logininfor:export
    日志: 记录导出操作

    参数:
        login_log_page_query: 查询条件（筛选要导出的日志）

    返回:
        StreamingResponse: Excel 文件流
    """
    # 获取全量数据（不分页）
    login_log_query_result = await LoginLogService.get_login_log_list_services(
        query_db, login_log_page_query, is_page=False
    )
    login_log_export_result = await LoginLogService.export_login_log_list_services(login_log_query_result)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(login_log_export_result))
