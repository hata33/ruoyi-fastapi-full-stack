"""
缓存监控控制器模块

本模块处理系统缓存监控的所有 HTTP 请求，包括：
- Redis 缓存统计信息查询（内存使用、键数量等）
- 缓存名称、键、值的查询
- 缓存清理操作（按名称、键、全部清理）

主要依赖：
- FastAPI: Web 框架，处理路由和请求
- Redis: 缓存数据库（通过 request.app.state.redis 访问）
- CacheService: 缓存相关业务逻辑

作者: RuoYi Team
"""

# FastAPI 核心组件
from fastapi import APIRouter, Depends, Request
from typing import List

# AOP 切面：权限控制
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth

# 数据模型（VO）
from module_admin.entity.vo.cache_vo import CacheInfoModel, CacheMonitorModel

# 业务服务层
from module_admin.service.cache_service import CacheService
from module_admin.service.login_service import LoginService

# 工具类
from utils.log_util import logger
from utils.response_util import ResponseUtil


# ==================== 路由配置 ====================
# 创建缓存监控路由器
# prefix: 所有接口的路径前缀为 /monitor/cache
# dependencies: 全局依赖，所有接口都需要先验证用户登录状态
cacheController = APIRouter(prefix='/monitor/cache', dependencies=[Depends(LoginService.get_current_user)])


# ==================== 缓存统计信息接口 ====================

@cacheController.get(
    '', response_model=CacheMonitorModel, dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))]
)
async def get_monitor_cache_info(request: Request):
    """
    获取缓存监控统计信息

    返回 Redis 服务器的详细统计信息，包括：
    - Redis 版本、运行时间
    - 内存使用情况
    - 键的总数量
    - 命中和未命中的统计

    权限: monitor:cache:list

    返回:
        CacheMonitorModel: 缓存监控统计信息
    """
    # 调用服务层获取 Redis 统计信息
    cache_info_query_result = await CacheService.get_cache_monitor_statistical_info_services(request)
    logger.info('获取成功')

    return ResponseUtil.success(data=cache_info_query_result)


# ==================== 缓存查询接口 ====================

@cacheController.get(
    '/getNames',
    response_model=List[CacheInfoModel],
    dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))],
)
async def get_monitor_cache_name(request: Request):
    """
    获取所有缓存名称列表

    查询 Redis 中所有已注册的缓存名称（如 sys_config、sys_dict 等）。

    权限: monitor:cache:list

    返回:
        List[CacheInfoModel]: 缓存名称列表
    """
    # 获取所有缓存名称
    cache_name_list_result = await CacheService.get_cache_monitor_cache_name_services()
    logger.info('获取成功')

    return ResponseUtil.success(data=cache_name_list_result)


@cacheController.get(
    '/getKeys/{cache_name}',
    response_model=List[str],
    dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))],
)
async def get_monitor_cache_key(request: Request, cache_name: str):
    """
    获取指定缓存名称下的所有键

    根据缓存名称查询该缓存下的所有键。

    权限: monitor:cache:list

    参数:
        cache_name: 缓存名称（如 sys_config）

    返回:
        List[str]: 键列表
    """
    # 获取指定缓存名称下的所有键
    cache_key_list_result = await CacheService.get_cache_monitor_cache_key_services(request, cache_name)
    logger.info('获取成功')

    return ResponseUtil.success(data=cache_key_list_result)


@cacheController.get(
    '/getValue/{cache_name}/{cache_key}',
    response_model=CacheInfoModel,
    dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))],
)
async def get_monitor_cache_value(request: Request, cache_name: str, cache_key: str):
    """
    获取指定键的缓存值

    根据缓存名称和键查询对应的值内容。

    权限: monitor:cache:list

    参数:
        cache_name: 缓存名称
        cache_key: 缓存键

    返回:
        CacheInfoModel: 缓存值信息
    """
    # 获取指定键的值
    cache_value_list_result = await CacheService.get_cache_monitor_cache_value_services(request, cache_name, cache_key)
    logger.info('获取成功')

    return ResponseUtil.success(data=cache_value_list_result)


# ==================== 缓存清理接口 ====================

@cacheController.delete(
    '/clearCacheName/{cache_name}', dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))]
)
async def clear_monitor_cache_name(request: Request, cache_name: str):
    """
    清理指定缓存名称下的所有缓存

    删除指定缓存名称下的所有键值对。

    权限: monitor:cache:list

    参数:
        cache_name: 缓存名称

    返回:
        dict: 操作结果消息
    """
    # 清理指定缓存名称下的所有缓存
    clear_cache_name_result = await CacheService.clear_cache_monitor_cache_name_services(request, cache_name)
    logger.info(clear_cache_name_result.message)

    return ResponseUtil.success(msg=clear_cache_name_result.message)


@cacheController.delete(
    '/clearCacheKey/{cache_key}', dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))]
)
async def clear_monitor_cache_key(request: Request, cache_key: str):
    """
    清理指定的缓存键

    删除指定的缓存键及其值。

    权限: monitor:cache:list

    参数:
        cache_key: 缓存键

    返回:
        dict: 操作结果消息
    """
    # 清理指定的缓存键
    clear_cache_key_result = await CacheService.clear_cache_monitor_cache_key_services(request, cache_key)
    logger.info(clear_cache_key_result.message)

    return ResponseUtil.success(msg=clear_cache_key_result.message)


@cacheController.delete('/clearCacheAll', dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))])
async def clear_monitor_cache_all(request: Request):
    """
    清理所有缓存

    清空 Redis 中的所有缓存数据。

    权限: monitor:cache:list

    返回:
        dict: 操作结果消息
    """
    # 清理所有缓存
    clear_cache_all_result = await CacheService.clear_cache_monitor_all_services(request)
    logger.info(clear_cache_all_result.message)

    return ResponseUtil.success(msg=clear_cache_all_result.message)
