"""
每日任务分类控制器模块
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic_validation_decorator import ValidateFields
from typing import Optional

from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.login_service import LoginService
from module_task.entity.vo.daily_task_category_vo import (
    DailyTaskCategoryModel,
    DailyTaskCategoryPageQueryModel,
    DeleteDailyTaskCategoryModel,
)
from module_task.service.daily_task_category_service import DailyTaskCategoryService
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


dailyTaskCategoryController = APIRouter(
    prefix='/daily-task-category', dependencies=[Depends(LoginService.get_current_user)]
)


@dailyTaskCategoryController.get(
    '/list',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('daily:category:list'))],
)
async def get_category_list(
    category_name: Optional[str] = None,
    page_num: int = 1,
    page_size: int = 10,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    获取每日任务分类列表（分页）
    """
    from module_task.entity.vo.daily_task_category_vo import DailyTaskCategoryPageQueryModel
    category_page_query = DailyTaskCategoryPageQueryModel(
        category_name=category_name,
        page_num=page_num,
        page_size=page_size,
    )

    # 设置当前用户ID过滤
    category_page_query.user_id = current_user.user.user_id

    category_page_query_result = await DailyTaskCategoryService.get_category_list_services(
        query_db, category_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=category_page_query_result)


@dailyTaskCategoryController.post(
    '', dependencies=[Depends(CheckUserInterfaceAuth('daily:category:add'))]
)
@ValidateFields(validate_model='add_category')
@Log(title='每日任务分类', business_type=BusinessType.INSERT)
async def add_category(
    request: Request,
    add_category: DailyTaskCategoryModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    添加每日任务分类
    """
    add_category.create_by = current_user.user.user_name
    add_category.create_time = datetime.now()
    add_category.update_by = current_user.user.user_name
    add_category.update_time = datetime.now()
    add_category.user_id = current_user.user.user_id
    add_category_result = await DailyTaskCategoryService.add_category_services(
        query_db, add_category
    )
    logger.info(add_category_result.message)

    return ResponseUtil.success(msg=add_category_result.message)


@dailyTaskCategoryController.put(
    '', dependencies=[Depends(CheckUserInterfaceAuth('daily:category:edit'))]
)
@ValidateFields(validate_model='edit_category')
@Log(title='每日任务分类', business_type=BusinessType.UPDATE)
async def edit_category(
    request: Request,
    edit_category: DailyTaskCategoryModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    编辑每日任务分类
    """
    edit_category.update_by = current_user.user.user_name
    edit_category.update_time = datetime.now()
    edit_category_result = await DailyTaskCategoryService.edit_category_services(
        query_db, edit_category
    )
    logger.info(edit_category_result.message)

    return ResponseUtil.success(msg=edit_category_result.message)


@dailyTaskCategoryController.delete(
    '/{category_ids}', dependencies=[Depends(CheckUserInterfaceAuth('daily:category:remove'))]
)
@Log(title='每日任务分类', business_type=BusinessType.DELETE)
async def delete_category(category_ids: str, query_db: AsyncSession = Depends(get_db)):
    """
    删除每日任务分类
    """
    delete_category = DeleteDailyTaskCategoryModel(category_ids=category_ids)
    delete_category_result = await DailyTaskCategoryService.delete_category_services(
        query_db, delete_category
    )
    logger.info(delete_category_result.message)

    return ResponseUtil.success(msg=delete_category_result.message)
