"""
通知公告控制器模块

本模块处理系统通知公告的所有 HTTP 请求，包括：
- 通知公告的增删改查（CRUD）操作
- 支持公告类型（通知、公告）

主要依赖：
- FastAPI: Web 框架，处理路由和请求
- SQLAlchemy: 数据库 ORM

作者: RuoYi Team
"""

from datetime import datetime

# FastAPI 核心组件
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic_validation_decorator import ValidateFields

# 配置相关
from config.enums import BusinessType
from config.get_db import get_db

# AOP 切面：权限控制、日志记录
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth

# 数据模型（VO）
from module_admin.entity.vo.notice_vo import DeleteNoticeModel, NoticeModel, NoticePageQueryModel
from module_admin.entity.vo.user_vo import CurrentUserModel

# 业务服务层
from module_admin.service.login_service import LoginService
from module_admin.service.notice_service import NoticeService

# 工具类
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


# ==================== 路由配置 ====================
# 创建通知公告路由器
# prefix: 所有接口的路径前缀为 /system/notice
# dependencies: 全局依赖，所有接口都需要先验证用户登录状态
noticeController = APIRouter(prefix='/system/notice', dependencies=[Depends(LoginService.get_current_user)])


# ==================== 通知公告查询接口 ====================

@noticeController.get(
    '/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('system:notice:list'))]
)
async def get_system_notice_list(
    request: Request,
    notice_page_query: NoticePageQueryModel = Depends(NoticePageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
):
    """
    获取通知公告列表（分页）

    根据查询条件获取通知公告列表，支持分页、排序、搜索等功能。

    权限: system:notice:list

    参数:
        notice_page_query: 分页查询参数（页码、每页数量、搜索条件等）

    返回:
        PageResponseModel: 分页结果，包含通知公告列表和分页信息
    """
    # 调用服务层获取分页数据
    notice_page_query_result = await NoticeService.get_notice_list_services(query_db, notice_page_query, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=notice_page_query_result)


@noticeController.get(
    '/{notice_id}', response_model=NoticeModel, dependencies=[Depends(CheckUserInterfaceAuth('system:notice:query'))]
)
async def query_detail_system_post(request: Request, notice_id: int, query_db: AsyncSession = Depends(get_db)):
    """
    获取通知公告详细信息

    查询指定通知公告的详细资料，用于编辑时回显数据。

    权限: system:notice:query

    参数:
        notice_id: 通知公告 ID

    返回:
        NoticeModel: 通知公告详细信息
    """
    notice_detail_result = await NoticeService.notice_detail_services(query_db, notice_id)
    logger.info(f'获取notice_id为{notice_id}的信息成功')

    return ResponseUtil.success(data=notice_detail_result)


# ==================== 通知公告增删改接口 ====================

@noticeController.post('', dependencies=[Depends(CheckUserInterfaceAuth('system:notice:add'))])
@ValidateFields(validate_model='add_notice')
@Log(title='通知公告', business_type=BusinessType.INSERT)
async def add_system_notice(
    request: Request,
    add_notice: NoticeModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    添加通知公告

    创建一个新的通知公告。
    支持的类型：通知（Notice）、公告（Announcement）。

    权限: system:notice:add
    日志: 记录通知公告添加操作

    参数:
        add_notice: 通知公告信息（标题、类型、内容、状态等）

    返回:
        dict: 操作结果消息
    """
    # 记录创建人和创建时间
    add_notice.create_by = current_user.user.user_name
    add_notice.create_time = datetime.now()
    add_notice.update_by = current_user.user.user_name
    add_notice.update_time = datetime.now()
    add_notice_result = await NoticeService.add_notice_services(query_db, add_notice)
    logger.info(add_notice_result.message)

    return ResponseUtil.success(msg=add_notice_result.message)


@noticeController.put('', dependencies=[Depends(CheckUserInterfaceAuth('system:notice:edit'))])
@ValidateFields(validate_model='edit_notice')
@Log(title='通知公告', business_type=BusinessType.UPDATE)
async def edit_system_notice(
    request: Request,
    edit_notice: NoticeModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    编辑通知公告

    更新现有的通知公告信息。

    权限: system:notice:edit
    日志: 记录通知公告编辑操作

    参数:
        edit_notice: 要更新的通知公告信息

    返回:
        dict: 操作结果消息
    """
    # 记录修改人和修改时间
    edit_notice.update_by = current_user.user.user_name
    edit_notice.update_time = datetime.now()
    edit_notice_result = await NoticeService.edit_notice_services(query_db, edit_notice)
    logger.info(edit_notice_result.message)

    return ResponseUtil.success(msg=edit_notice_result.message)


@noticeController.delete('/{notice_ids}', dependencies=[Depends(CheckUserInterfaceAuth('system:notice:remove'))])
@Log(title='通知公告', business_type=BusinessType.DELETE)
async def delete_system_notice(request: Request, notice_ids: str, query_db: AsyncSession = Depends(get_db)):
    """
    删除通知公告

    批量删除通知公告，支持一次删除多个（用逗号分隔 ID）。

    权限: system:notice:remove
    日志: 记录通知公告删除操作

    参数:
        notice_ids: 要删除的通知公告 ID 列表，逗号分隔（如 "1,2,3"）

    返回:
        dict: 操作结果消息
    """
    delete_notice = DeleteNoticeModel(noticeIds=notice_ids)
    delete_notice_result = await NoticeService.delete_notice_services(query_db, delete_notice)
    logger.info(delete_notice_result.message)

    return ResponseUtil.success(msg=delete_notice_result.message)
