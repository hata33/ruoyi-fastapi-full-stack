"""
系统参数配置控制器模块

本模块处理系统参数配置的所有 HTTP 请求，包括：
- 系统参数的增删改查（CRUD）操作
- 参数配置缓存刷新
- 参数配置导出
- 根据参数键查询参数值

主要依赖：
- FastAPI: Web 框架，处理路由和请求
- SQLAlchemy: 数据库 ORM
- Redis: 缓存参数配置，提高查询性能

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
from module_admin.entity.vo.config_vo import ConfigModel, ConfigPageQueryModel, DeleteConfigModel
from module_admin.entity.vo.user_vo import CurrentUserModel

# 业务服务层
from module_admin.service.config_service import ConfigService
from module_admin.service.login_service import LoginService

# 工具类
from utils.common_util import bytes2file_response
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


# ==================== 路由配置 ====================
# 创建系统参数配置路由器
# prefix: 所有接口的路径前缀为 /system/config
# dependencies: 全局依赖，所有接口都需要先验证用户登录状态
configController = APIRouter(prefix='/system/config', dependencies=[Depends(LoginService.get_current_user)])


# ==================== 参数配置查询接口 ====================

@configController.get(
    '/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('system:config:list'))]
)
async def get_system_config_list(
    request: Request,
    config_page_query: ConfigPageQueryModel = Depends(ConfigPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
):
    """
    获取系统参数配置列表（分页）

    根据查询条件获取系统参数配置列表，支持分页、排序、搜索等功能。

    权限: system:config:list

    参数:
        config_page_query: 分页查询参数（页码、每页数量、搜索条件等）

    返回:
        PageResponseModel: 分页结果，包含参数配置列表和分页信息
    """
    # 调用服务层获取分页数据
    config_page_query_result = await ConfigService.get_config_list_services(query_db, config_page_query, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=config_page_query_result)


@configController.get(
    '/{config_id}', response_model=ConfigModel, dependencies=[Depends(CheckUserInterfaceAuth('system:config:query'))]
)
async def query_detail_system_config(request: Request, config_id: int, query_db: AsyncSession = Depends(get_db)):
    """
    获取参数配置详细信息

    查询指定参数配置的详细资料，用于编辑时回显数据。

    权限: system:config:query

    参数:
        config_id: 参数配置 ID

    返回:
        ConfigModel: 参数配置详细信息
    """
    config_detail_result = await ConfigService.config_detail_services(query_db, config_id)
    logger.info(f'获取config_id为{config_id}的信息成功')

    return ResponseUtil.success(data=config_detail_result)


@configController.get('/configKey/{config_key}')
async def query_system_config(request: Request, config_key: str):
    """
    根据参数键查询参数值

    根据参数键（config_key）查询对应的参数值。
    优先从缓存中读取，提高查询性能。
    无需权限校验，供系统内部调用。

    参数:
        config_key: 参数键（如 sys.account.captchaEnabled）

    返回:
        str: 参数值
    """
    # 从缓存中获取参数值（提高性能）
    config_query_result = await ConfigService.query_config_list_from_cache_services(request.app.state.redis, config_key)
    logger.info('获取成功')

    return ResponseUtil.success(msg=config_query_result)


# ==================== 参数配置增删改接口 ====================

@configController.post('', dependencies=[Depends(CheckUserInterfaceAuth('system:config:add'))])
@ValidateFields(validate_model='add_config')
@Log(title='参数管理', business_type=BusinessType.INSERT)
async def add_system_config(
    request: Request,
    add_config: ConfigModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    添加系统参数配置

    创建一个新的系统参数配置。
    添加后会自动刷新缓存。

    权限: system:config:add
    日志: 记录参数添加操作

    参数:
        add_config: 参数配置信息（参数键、参数值、参数类型等）

    返回:
        dict: 操作结果消息
    """
    # 记录创建人和创建时间
    add_config.create_by = current_user.user.user_name
    add_config.create_time = datetime.now()
    add_config.update_by = current_user.user.user_name
    add_config.update_time = datetime.now()
    add_config_result = await ConfigService.add_config_services(request, query_db, add_config)
    logger.info(add_config_result.message)

    return ResponseUtil.success(msg=add_config_result.message)


@configController.put('', dependencies=[Depends(CheckUserInterfaceAuth('system:config:edit'))])
@ValidateFields(validate_model='edit_config')
@Log(title='参数管理', business_type=BusinessType.UPDATE)
async def edit_system_config(
    request: Request,
    edit_config: ConfigModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    编辑系统参数配置

    更新现有的系统参数配置。
    更新后会自动刷新缓存。

    权限: system:config:edit
    日志: 记录参数编辑操作

    参数:
        edit_config: 要更新的参数配置信息

    返回:
        dict: 操作结果消息
    """
    # 记录修改人和修改时间
    edit_config.update_by = current_user.user.user_name
    edit_config.update_time = datetime.now()
    edit_config_result = await ConfigService.edit_config_services(request, query_db, edit_config)
    logger.info(edit_config_result.message)

    return ResponseUtil.success(msg=edit_config_result.message)


@configController.delete('/{config_ids}', dependencies=[Depends(CheckUserInterfaceAuth('system:config:remove'))])
@Log(title='参数管理', business_type=BusinessType.DELETE)
async def delete_system_config(request: Request, config_ids: str, query_db: AsyncSession = Depends(get_db)):
    """
    删除系统参数配置

    批量删除参数配置，支持一次删除多个配置（用逗号分隔 ID）。

    权限: system:config:remove
    日志: 记录参数删除操作

    参数:
        config_ids: 要删除的参数配置 ID 列表，逗号分隔（如 "1,2,3"）

    返回:
        dict: 操作结果消息
    """
    delete_config = DeleteConfigModel(configIds=config_ids)
    delete_config_result = await ConfigService.delete_config_services(request, query_db, delete_config)
    logger.info(delete_config_result.message)

    return ResponseUtil.success(msg=delete_config_result.message)


# ==================== 缓存管理接口 ====================

@configController.delete('/refreshCache', dependencies=[Depends(CheckUserInterfaceAuth('system:config:remove'))])
@Log(title='参数管理', business_type=BusinessType.UPDATE)
async def refresh_system_config(request: Request, query_db: AsyncSession = Depends(get_db)):
    """
    刷新参数配置缓存

    重新加载系统参数配置到 Redis 缓存中。
    用于在修改数据库后手动刷新缓存。

    权限: system:config:remove
    日志: 记录缓存刷新操作

    返回:
        dict: 操作结果消息
    """
    refresh_config_result = await ConfigService.refresh_sys_config_services(request, query_db)
    logger.info(refresh_config_result.message)

    return ResponseUtil.success(msg=refresh_config_result.message)


# ==================== 导出接口 ====================

@configController.post('/export', dependencies=[Depends(CheckUserInterfaceAuth('system:config:export'))])
@Log(title='参数管理', business_type=BusinessType.EXPORT)
async def export_system_config_list(
    request: Request,
    config_page_query: ConfigPageQueryModel = Form(),
    query_db: AsyncSession = Depends(get_db),
):
    """
    导出参数配置列表

    根据查询条件导出参数配置数据到 Excel 文件。

    权限: system:config:export
    日志: 记录导出操作

    参数:
        config_page_query: 查询条件（筛选要导出的参数配置）

    返回:
        StreamingResponse: Excel 文件流
    """
    # 获取全量数据（不分页）
    config_query_result = await ConfigService.get_config_list_services(query_db, config_page_query, is_page=False)
    config_export_result = await ConfigService.export_config_list_services(config_query_result)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(config_export_result))
