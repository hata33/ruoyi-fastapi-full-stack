"""
岗位管理控制器模块

本模块处理系统岗位管理的所有 HTTP 请求，包括：
- 岗位的增删改查（CRUD）操作
- 岗位导出功能

主要依赖：
- FastAPI: Web 框架，处理路由和请求
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
from module_admin.entity.vo.post_vo import DeletePostModel, PostModel, PostPageQueryModel
from module_admin.entity.vo.user_vo import CurrentUserModel

# 业务服务层
from module_admin.service.login_service import LoginService
from module_admin.service.post_service import PostService

# 工具类
from utils.common_util import bytes2file_response
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


# ==================== 路由配置 ====================
# 创建岗位管理路由器
# prefix: 所有接口的路径前缀为 /system/post
# dependencies: 全局依赖，所有接口都需要先验证用户登录状态
postController = APIRouter(prefix='/system/post', dependencies=[Depends(LoginService.get_current_user)])


# ==================== 岗位查询接口 ====================

@postController.get(
    '/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('system:post:list'))]
)
async def get_system_post_list(
    request: Request,
    post_page_query: PostPageQueryModel = Depends(PostPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
):
    """
    获取岗位列表（分页）

    根据查询条件获取岗位列表，支持分页、排序、搜索等功能。

    权限: system:post:list

    参数:
        post_page_query: 分页查询参数（页码、每页数量、搜索条件等）

    返回:
        PageResponseModel: 分页结果，包含岗位列表和分页信息
    """
    # 调用服务层获取分页数据
    post_page_query_result = await PostService.get_post_list_services(query_db, post_page_query, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=post_page_query_result)


@postController.get(
    '/{post_id}', response_model=PostModel, dependencies=[Depends(CheckUserInterfaceAuth('system:post:query'))]
)
async def query_detail_system_post(request: Request, post_id: int, query_db: AsyncSession = Depends(get_db)):
    """
    获取岗位详细信息

    查询指定岗位的详细资料，用于编辑时回显数据。

    权限: system:post:query

    参数:
        post_id: 岗位 ID

    返回:
        PostModel: 岗位详细信息
    """
    post_detail_result = await PostService.post_detail_services(query_db, post_id)
    logger.info(f'获取post_id为{post_id}的信息成功')

    return ResponseUtil.success(data=post_detail_result)


# ==================== 岗位增删改接口 ====================

@postController.post('', dependencies=[Depends(CheckUserInterfaceAuth('system:post:add'))])
@ValidateFields(validate_model='add_post')
@Log(title='岗位管理', business_type=BusinessType.INSERT)
async def add_system_post(
    request: Request,
    add_post: PostModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    添加岗位

    创建一个新的岗位。

    权限: system:post:add
    日志: 记录岗位添加操作

    参数:
        add_post: 岗位信息（岗位编码、岗位名称、排序等）

    返回:
        dict: 操作结果消息
    """
    # 记录创建人和创建时间
    add_post.create_by = current_user.user.user_name
    add_post.create_time = datetime.now()
    add_post.update_by = current_user.user.user_name
    add_post.update_time = datetime.now()
    add_post_result = await PostService.add_post_services(query_db, add_post)
    logger.info(add_post_result.message)

    return ResponseUtil.success(msg=add_post_result.message)


@postController.put('', dependencies=[Depends(CheckUserInterfaceAuth('system:post:edit'))])
@ValidateFields(validate_model='edit_post')
@Log(title='岗位管理', business_type=BusinessType.UPDATE)
async def edit_system_post(
    request: Request,
    edit_post: PostModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    编辑岗位

    更新现有的岗位信息。

    权限: system:post:edit
    日志: 记录岗位编辑操作

    参数:
        edit_post: 要更新的岗位信息

    返回:
        dict: 操作结果消息
    """
    # 记录修改人和修改时间
    edit_post.update_by = current_user.user.user_name
    edit_post.update_time = datetime.now()
    edit_post_result = await PostService.edit_post_services(query_db, edit_post)
    logger.info(edit_post_result.message)

    return ResponseUtil.success(msg=edit_post_result.message)


@postController.delete('/{post_ids}', dependencies=[Depends(CheckUserInterfaceAuth('system:post:remove'))])
@Log(title='岗位管理', business_type=BusinessType.DELETE)
async def delete_system_post(request: Request, post_ids: str, query_db: AsyncSession = Depends(get_db)):
    """
    删除岗位

    批量删除岗位，支持一次删除多个（用逗号分隔 ID）。

    权限: system:post:remove
    日志: 记录岗位删除操作

    参数:
        post_ids: 要删除的岗位 ID 列表，逗号分隔（如 "1,2,3"）

    返回:
        dict: 操作结果消息
    """
    delete_post = DeletePostModel(postIds=post_ids)
    delete_post_result = await PostService.delete_post_services(query_db, delete_post)
    logger.info(delete_post_result.message)

    return ResponseUtil.success(msg=delete_post_result.message)


# ==================== 岗位导出接口 ====================

@postController.post('/export', dependencies=[Depends(CheckUserInterfaceAuth('system:post:export'))])
@Log(title='岗位管理', business_type=BusinessType.EXPORT)
async def export_system_post_list(
    request: Request,
    post_page_query: PostPageQueryModel = Form(),
    query_db: AsyncSession = Depends(get_db),
):
    """
    导出岗位列表

    根据查询条件导出岗位数据到 Excel 文件。

    权限: system:post:export
    日志: 记录导出操作

    参数:
        post_page_query: 查询条件（筛选要导出的岗位）

    返回:
        StreamingResponse: Excel 文件流
    """
    # 获取全量数据（不分页）
    post_query_result = await PostService.get_post_list_services(query_db, post_page_query, is_page=False)
    post_export_result = await PostService.export_post_list_services(post_query_result)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(post_export_result))
