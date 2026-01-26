"""
通用文件控制器模块

本模块处理通用文件上传下载相关的 HTTP 请求，包括：
- 通用文件上传
- 通用文件下载
- 资源文件下载

主要依赖：
- FastAPI: Web 框架，处理路由和请求
- BackgroundTasks: 后台任务处理（如下载后删除临时文件）
- CommonService: 通用文件服务

作者: RuoYi Team
"""

# FastAPI 核心组件
from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, Request, UploadFile

# 业务服务层
from module_admin.service.common_service import CommonService
from module_admin.service.login_service import LoginService

# 工具类
from utils.log_util import logger
from utils.response_util import ResponseUtil


# ==================== 路由配置 ====================
# 创建通用文件路由器
# prefix: 所有接口的路径前缀为 /common
# dependencies: 全局依赖，所有接口都需要先验证用户登录状态
commonController = APIRouter(prefix='/common', dependencies=[Depends(LoginService.get_current_user)])


# ==================== 文件上传接口 ====================

@commonController.post('/upload')
async def common_upload(request: Request, file: UploadFile = File(...)):
    """
    通用文件上传接口

    上传文件到服务器，支持文件类型校验、大小限制等。
    上传的文件会按日期目录组织存储。

    参数:
        file: 上传的文件对象

    返回:
        dict: 包含文件访问 URL 的响应
    """
    # 调用通用服务处理文件上传
    upload_result = await CommonService.upload_service(request, file)
    logger.info('上传成功')

    return ResponseUtil.success(model_content=upload_result.result)


# ==================== 文件下载接口 ====================

@commonController.get('/download')
async def common_download(
    request: Request,
    background_tasks: BackgroundTasks,
    file_name: str = Query(alias='fileName'),
    delete: bool = Query(),
):
    """
    通用文件下载接口

    下载服务器上的文件。
    支持下载后自动删除临时文件（通过后台任务）。

    参数:
        file_name: 要下载的文件名
        delete: 是否在下载后删除文件

    返回:
        StreamingResponse: 文件流响应
    """
    # 调用通用服务处理文件下载
    download_result = await CommonService.download_services(background_tasks, file_name, delete)
    logger.info(download_result.message)

    return ResponseUtil.streaming(data=download_result.result)


@commonController.get('/download/resource')
async def common_download_resource(request: Request, resource: str = Query()):
    """
    资源文件下载接口

    下载系统资源文件（如头像、附件等）。
    资源路径通常是相对路径或虚拟路径。

    参数:
        resource: 资源路径

    返回:
        StreamingResponse: 文件流响应
    """
    # 调用通用服务处理资源文件下载
    download_resource_result = await CommonService.download_resource_services(resource)
    logger.info(download_resource_result.message)

    return ResponseUtil.streaming(data=download_resource_result.result)
