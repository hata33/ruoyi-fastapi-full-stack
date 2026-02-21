"""
文件管理模块 API 控制器（File Controller）

核心职责：
- 提供文件上传、下载、查询、更新、删除等完整的文件管理接口。
- 支持文件状态管理、处理进度查询、批量操作等功能。

整体设计要点：
1) 路由注册：使用 APIRouter 统一挂载在前缀 `/system/file` 下，默认依赖用户鉴权。
2) 权限控制：通过 `Depends(CheckUserInterfaceAuth('permission:code'))` 做接口级权限校验。
3) 字段校验：通过 `@ValidateFields(validate_model='...')` 对请求体绑定的 Pydantic 模型做服务端校验。
4) 操作日志：通过 `@Log(title=..., business_type=BusinessType.XXX)` 记录操作日志。
5) 依赖注入：
   - `Depends(get_db)` 注入 `AsyncSession`（数据库会话）。
   - `Depends(LoginService.get_current_user)` 注入当前登录用户。
6) 统一返回：使用 `ResponseUtil.success/streaming` 统一结构化响应。
7) 安全防护：文件类型验证、路径遍历防护、权限校验、并发控制。

高级/特殊点标注：
- 文件上传：使用 `UploadFile` 处理文件上传，支持大文件分片上传。
- 权限校验：只有文件上传者可以操作自己的文件。
- 状态管理：支持文件处理状态流转和进度查询。
- 软删除：使用软删除机制，避免数据丢失。
"""

from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, Path
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.file_vo import (
    FileCreateModel, FileModel, FilePageQueryModel, FileResponseModel,
    FileStatusUpdateModel, FileStatus, FileUploadResponseModel,
    FileProcessProgressModel, FileDeleteModel
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.file_service import FileService
from module_admin.service.login_service import LoginService
from utils.common_util import bytes2file_response
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


# 路由前缀统一为 /system/file
# 默认依赖当前用户鉴权：所有接口在进入控制器前都会先校验用户会话
fileController = APIRouter(
    prefix='/system/file', dependencies=[Depends(LoginService.get_current_user)]
)

# ========================= 文件上传相关接口 =========================


@fileController.post(
    '/upload',
    response_model=FileUploadResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('system:file:upload'))]
)
@Log(title='文件上传', business_type=BusinessType.INSERT)
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description='上传的文件'),
    project_id: str = Form(..., description='项目ID'),
    project_name: str = Form(None, description='项目名称'),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    文件上传接口

    功能：上传文件到系统，支持txt和md格式。
    安全：文件类型验证、大小限制、路径验证、去重处理。

    :param request: Request对象
    :param file: 上传的文件
    :param project_id: 项目ID
    :param project_name: 项目名称
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 上传结果
    """
    upload_result = await FileService.upload_file_services(
        request=request,
        query_db=query_db,
        file=file,
        project_id=project_id,
        project_name=project_name,
        user_id=current_user.user.user_id,
        username=current_user.user.user_name
    )

    logger.info(f'用户 {current_user.user.user_name} 上传文件 {file.filename} 成功')
    return ResponseUtil.success(data=upload_result, msg='文件上传成功')


# ========================= 文件查询相关接口 =========================

@fileController.get(
    '/list',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('system:file:list'))]
)
async def get_file_list(
    request: Request,
    file_page_query: FilePageQueryModel = Depends(FilePageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    获取文件列表接口

    功能：分页查询文件列表，支持条件过滤。
    安全：只返回当前用户有权限访问的文件。

    :param request: Request对象
    :param file_page_query: 分页查询参数
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 文件列表
    """
    # 限制只能查询自己的文件
    file_page_query.upload_user_id = current_user.user.user_id

    file_list_result = await FileService.get_file_list_services(
        query_db, file_page_query, is_page=True
    )

    logger.info('获取文件列表成功')
    return ResponseUtil.success(model_content=file_list_result)


@fileController.get(
    '/{file_id}',
    response_model=FileResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('system:file:query'))]
)
async def get_file_detail(
    request: Request,
    file_id: int = Path(
        ...,
        regex=r'^\d+$',  # 仅允许数字字符
        description='文件ID（纯数字）',
        example=123
    ),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    获取文件详情接口

    功能：根据文件ID查询文件详情。
    安全：权限校验，只有文件上传者可以查看。

    :param request: Request对象
    :param file_id: 文件ID
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 文件详情
    """
    file_detail_result = await FileService.get_file_detail_services(query_db, file_id)

    # 检查权限
    if file_detail_result.file_id and file_detail_result.upload_user_id != current_user.user.user_id:
        return ResponseUtil.forbidden(msg='无权限访问该文件')

    logger.info(f'获取文件 {file_id} 详情成功')
    return ResponseUtil.success(data=file_detail_result)


@fileController.get(
    '/user/files',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('system:file:list'))]
)
async def get_user_files(
    request: Request,
    is_page: bool = True,
    page_num: int = 1,
    page_size: int = 10,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    获取用户文件列表接口

    功能：获取当前用户上传的所有文件。

    :param request: Request对象
    :param is_page: 是否分页
    :param page_num: 当前页码
    :param page_size: 每页记录数
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 用户文件列表
    """
    user_files_result = await FileService.get_user_files_services(
        query_db, current_user.user.user_id, is_page, page_num, page_size
    )

    logger.info(f'获取用户 {current_user.user.user_name} 文件列表成功')
    return ResponseUtil.success(model_content=user_files_result)


@fileController.get(
    '/project/{project_id}',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('system:file:list'))]
)
async def get_project_files(
    request: Request,
    project_id: str,
    is_page: bool = True,
    page_num: int = 1,
    page_size: int = 10,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    获取项目文件列表接口

    功能：获取指定项目的所有文件。

    :param request: Request对象
    :param project_id: 项目ID
    :param is_page: 是否分页
    :param page_num: 当前页码
    :param page_size: 每页记录数
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 项目文件列表
    """
    project_files_result = await FileService.get_project_files_services(
        query_db, project_id, is_page, page_num, page_size
    )

    logger.info(f'获取项目 {project_id} 文件列表成功')
    return ResponseUtil.success(model_content=project_files_result)


@fileController.get(
    '/status/{file_status}',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('system:file:list'))]
)
async def get_files_by_status(
    request: Request,
    file_status: FileStatus,
    is_page: bool = True,
    page_num: int = 1,
    page_size: int = 10,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    根据状态获取文件列表接口

    功能：获取指定状态的文件列表，用于监控和运维。

    :param request: Request对象
    :param file_status: 文件状态
    :param is_page: 是否分页
    :param page_num: 当前页码
    :param page_size: 每页记录数
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 文件列表
    """
    files_by_status_result = await FileService.get_files_by_status_services(
        query_db, file_status, is_page, page_num, page_size
    )

    logger.info(f'获取状态为 {file_status.value} 的文件列表成功')
    return ResponseUtil.success(model_content=files_by_status_result)


# ========================= 文件状态管理相关接口 =========================

@fileController.patch(
    '/{file_id}/status',
    dependencies=[Depends(CheckUserInterfaceAuth('system:file:edit'))]
)
@ValidateFields(validate_model='update_file_status')
@Log(title='文件状态更新', business_type=BusinessType.UPDATE)
async def update_file_status(
    request: Request,
    file_id: int,
    status_data: FileStatusUpdateModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    更新文件状态接口

    功能：更新文件处理状态，包括重试次数和错误信息。
    安全：权限校验，只有文件上传者可以更新。

    :param request: Request对象
    :param file_id: 文件ID
    :param status_data: 状态更新数据
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 更新结果
    """
    status_data.update_by = current_user.user.user_name

    update_result = await FileService.update_file_status_services(
        query_db, file_id, status_data, current_user.user.user_id
    )

    logger.info(f'文件 {file_id} 状态更新为 {status_data.file_status.value} 成功')
    return ResponseUtil.success(msg=update_result.message)


@fileController.get(
    '/{file_id}/progress',
    response_model=FileProcessProgressModel,
    dependencies=[Depends(CheckUserInterfaceAuth('system:file:query'))]
)
async def get_file_process_progress(
    request: Request,
    file_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    获取文件处理进度接口

    功能：查询文件处理进度和状态信息。

    :param request: Request对象
    :param file_id: 文件ID
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 处理进度信息
    """
    progress_result = await FileService.get_file_process_progress_services(
        query_db, file_id, current_user.user.user_id
    )

    logger.info(f'获取文件 {file_id} 处理进度成功')
    return ResponseUtil.success(data=progress_result)


@fileController.post(
    '/{file_id}/retry',
    dependencies=[Depends(CheckUserInterfaceAuth('system:file:edit'))]
)
@Log(title='文件重试', business_type=BusinessType.UPDATE)
async def retry_failed_file(
    request: Request,
    file_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    重试失败文件接口

    功能：重新处理失败的文件。

    :param request: Request对象
    :param file_id: 文件ID
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 重试结果
    """
    retry_result = await FileService.retry_failed_file_services(
        query_db, file_id, current_user.user.user_id
    )

    logger.info(f'文件 {file_id} 重试成功')
    return ResponseUtil.success(msg=retry_result.message)


# ========================= 文件删除相关接口 =========================


@fileController.delete(
    '/batch',
    dependencies=[Depends(CheckUserInterfaceAuth('system:file:remove'))]
)
@Log(title='批量删除文件', business_type=BusinessType.DELETE)
async def batch_delete_files(
    request: Request,
    file_ids: str = Form(..., description='文件ID列表，多个用逗号分隔'),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    批量删除文件接口

    功能：批量软删除多个文件。
    安全：权限校验，只有文件上传者可以删除自己的文件。

    :param request: Request对象
    :param file_ids: 文件ID列表（逗号分隔）
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 删除结果
    """
    delete_result = await FileService.batch_delete_files_services(
        query_db, file_ids, current_user.user.user_id, current_user.user.user_name
    )

    logger.info(f'用户 {current_user.user.user_name} 批量删除文件 {file_ids} 成功')
    return ResponseUtil.success(msg=delete_result.message)


@fileController.delete(
    '/{file_id}',
    dependencies=[Depends(CheckUserInterfaceAuth('system:file:remove'))]
)
@Log(title='文件删除', business_type=BusinessType.DELETE)
async def delete_file(
    request: Request,
    file_id: int = Path(
        ...,  # 必填参数
        regex=r"^\d+$",  # 无空格！纯数字匹配（^开头，$结尾，\d+一个以上数字）
        ge=1,  # 额外约束：ID必须是正整数（避免0或负数）
        description="文件ID（仅支持纯数字，如1、10）",
        example=8  # 示例值，增强接口文档可读性
    ),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    删除文件接口

    功能：软删除文件记录。
    安全：权限校验，只有文件上传者可以删除。

    :param request: Request对象
    :param file_id: 文件ID
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 删除结果
    """
    delete_result = await FileService.delete_file_services(
        query_db, file_id, current_user.user.user_id, current_user.user.user_name
    )

    logger.info(f'用户 {current_user.user.user_name} 删除文件 {file_id} 成功')
    return ResponseUtil.success(msg=delete_result.message)


# ========================= 文件统计相关接口 =========================

@fileController.get(
    '/ops/statistics',
    dependencies=[Depends(CheckUserInterfaceAuth('system:file:list'))]
)
async def get_file_statistics(
    request: Request,
    project_id: str = None,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    获取文件统计信息接口

    功能：提供文件管理仪表板统计信息。

    :param request: Request对象
    :param project_id: 项目ID（可选）
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 统计信息
    """
    statistics_result = await FileService.get_file_statistics_services(
        query_db, current_user.user.user_id, project_id
    )

    logger.info(f'获取用户 {current_user.user.user_name} 文件统计信息成功')
    return ResponseUtil.success(data=statistics_result)


# ========================= 文件下载相关接口 =========================

@fileController.get(
    '/{file_id}/download',
    dependencies=[Depends(CheckUserInterfaceAuth('system:file:download'))]
)
@Log(title='文件下载', business_type=BusinessType.OTHER)
async def download_file(
    request: Request,
    file_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    文件下载接口

    功能：下载指定文件。
    安全：权限校验，只有文件上传者可以下载。

    :param request: Request对象
    :param file_id: 文件ID
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 文件流
    """
    # 获取文件信息
    file_detail = await FileService.get_file_detail_services(query_db, file_id)

    if not file_detail.file_id:
        return ResponseUtil.error(msg='文件不存在')

    # 检查权限
    if file_detail.upload_user_id != current_user.user.user_id:
        return ResponseUtil.forbidden(msg='无权限下载该文件')

    # 检查文件状态
    # if file_detail.file_status != FileStatus.COMPLETED:
    #     return ResponseUtil.error(msg='文件尚未处理完成，无法下载')

    # 读取文件内容
    try:
        with open(file_detail.file_path, 'rb') as f:
            file_content = f.read()

        logger.info(
            f'用户 {current_user.user.user_name} 下载文件 {file_detail.original_filename} 成功')

        # 返回文件流
        return ResponseUtil.streaming(
            data=bytes2file_response(
                file_content)
        )

    except FileNotFoundError:
        return ResponseUtil.error(msg='文件不存在于磁盘')
    except Exception as e:
        logger.error(f'文件下载失败: {str(e)}')
        return ResponseUtil.error(msg='文件下载失败')


# ========================= 文件清理相关接口 =========================

@fileController.post(
    '/cleanup',
    dependencies=[Depends(CheckUserInterfaceAuth('system:file:remove'))]
)
@Log(title='文件清理', business_type=BusinessType.CLEAN)
async def cleanup_deleted_files(
    request: Request,
    days: int = 30,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    清理已删除文件接口

    功能：清理指定天数前软删除的文件记录（物理删除）。
    注意：这是危险操作，需要管理员权限。

    :param request: Request对象
    :param days: 保留天数
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 清理结果
    """
    cleanup_result = await FileService.cleanup_deleted_files_services(query_db, days)

    logger.info(f'用户 {current_user.user.user_name} 清理 {days} 天前删除的文件成功')
    return ResponseUtil.success(msg=cleanup_result.message)
