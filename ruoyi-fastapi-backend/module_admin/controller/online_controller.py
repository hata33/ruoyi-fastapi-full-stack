"""
在线用户监控控制器模块

本模块处理在线用户监控的所有 HTTP 请求，包括：
- 在线用户列表查询
- 强制用户退出登录

主要依赖：
- FastAPI: Web 框架，处理路由和请求
- Redis: 存储在线用户会话信息

作者: RuoYi Team
"""

# FastAPI 核心组件
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

# 配置相关
from config.enums import BusinessType
from config.get_db import get_db

# AOP 切面：权限控制、日志记录
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth

# 数据模型（VO）
from module_admin.entity.vo.online_vo import DeleteOnlineModel, OnlineQueryModel

# 业务服务层
from module_admin.service.login_service import LoginService
from module_admin.service.online_service import OnlineService

# 工具类
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


# ==================== 路由配置 ====================
# 创建在线用户监控路由器
# prefix: 所有接口的路径前缀为 /monitor/online
# dependencies: 全局依赖，所有接口都需要先验证用户登录状态
onlineController = APIRouter(prefix='/monitor/online', dependencies=[Depends(LoginService.get_current_user)])


# ==================== 在线用户查询接口 ====================

@onlineController.get(
    '/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('monitor:online:list'))]
)
async def get_monitor_online_list(
    request: Request, online_page_query: OnlineQueryModel = Depends(OnlineQueryModel.as_query)
):
    """
    获取在线用户列表（分页）

    根据查询条件获取当前在线的用户列表。
    在线用户信息从 Redis 中获取，包括用户名、登录时间、登录 IP 等。

    权限: monitor:online:list

    参数:
        online_page_query: 分页查询参数（页码、每页数量、搜索条件等）

    返回:
        PageResponseModel: 分页结果，包含在线用户列表和分页信息
    """
    # 从 Redis 获取在线用户数据（全量）
    online_query_result = await OnlineService.get_online_list_services(request, online_page_query)
    logger.info('获取成功')

    return ResponseUtil.success(
        model_content=PageResponseModel(rows=online_query_result, total=len(online_query_result))
    )


# ==================== 在线用户管理接口 ====================

@onlineController.delete('/{token_ids}', dependencies=[Depends(CheckUserInterfaceAuth('monitor:online:forceLogout'))])
@Log(title='在线用户', business_type=BusinessType.FORCE)
async def delete_monitor_online(request: Request, token_ids: str, query_db: AsyncSession = Depends(get_db)):
    """
    强制用户退出登录

    强制指定的在线用户退出登录系统。
    会删除 Redis 中的会话信息，用户需要重新登录。

    权限: monitor:online:forceLogout
    日志: 记录强制退出操作

    参数:
        token_ids: 要强制退出的会话 ID 列表，逗号分隔（如 "xxx,yyy,zzz"）

    返回:
        dict: 操作结果消息
    """
    delete_online = DeleteOnlineModel(tokenIds=token_ids)
    delete_online_result = await OnlineService.delete_online_services(request, delete_online)
    logger.info(delete_online_result.message)

    return ResponseUtil.success(msg=delete_online_result.message)
