"""
服务器监控控制器模块

本模块处理服务器监控的所有 HTTP 请求，包括：
- 服务器系统信息查询（CPU、内存、磁盘、JVM 等）

主要依赖：
- FastAPI: Web 框架，处理路由和请求
- psutil: 系统信息获取库

作者: RuoYi Team
"""

# FastAPI 核心组件
from fastapi import APIRouter, Depends, Request

# AOP 切面：权限控制
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth

# 数据模型（VO）
from module_admin.entity.vo.server_vo import ServerMonitorModel

# 业务服务层
from module_admin.service.login_service import LoginService
from module_admin.service.server_service import ServerService

# 工具类
from utils.response_util import ResponseUtil
from utils.log_util import logger


# ==================== 路由配置 ====================
# 创建服务器监控路由器
# prefix: 所有接口的路径前缀为 /monitor/server
# dependencies: 全局依赖，所有接口都需要先验证用户登录状态
serverController = APIRouter(prefix='/monitor/server', dependencies=[Depends(LoginService.get_current_user)])


# ==================== 服务器监控接口 ====================

@serverController.get(
    '', response_model=ServerMonitorModel, dependencies=[Depends(CheckUserInterfaceAuth('monitor:server:list'))]
)
async def get_monitor_server_info(request: Request):
    """
    获取服务器监控信息

    获取服务器的详细监控信息，包括：
    - CPU 信息（型号、核心数、使用率）
    - 内存信息（总量、已用、空闲、使用率）
    - 服务器信息（操作系统、架构、主机名）
    - JVM 信息（运行时间、JDK 版本、内存信息）
    - 磁盘信息（各分区使用情况）

    权限: monitor:server:list

    返回:
        ServerMonitorModel: 服务器监控信息
    """
    # 调用服务层获取服务器监控信息
    server_info_query_result = await ServerService.get_server_monitor_info()
    logger.info('获取成功')

    return ResponseUtil.success(data=server_info_query_result)
