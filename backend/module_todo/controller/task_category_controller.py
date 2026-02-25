"""
任务分类控制器模块
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic_validation_decorator import ValidateFields

from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.login_service import LoginService
from module_todo.entity.vo.task_category_vo import TaskCategoryModel, TaskCategoryPageQueryModel
from module_todo.service.task_category_service import TaskCategoryService
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


taskCategoryController = APIRouter(prefix='/todo/task/category', dependencies=[Depends(LoginService.get_current_user)])


@taskCategoryController.get(
    '/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('todo:task:category:list'))]
)
async def get_category_list(
    request: Request,
    category_page_query: TaskCategoryPageQueryModel = Depends(TaskCategoryPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
):
    """
    获取分类列表（分页）
    """
    # 设置当前用户ID过滤
    current_user: CurrentUserModel = await LoginService.get_current_user(request)
    category_page_query.user_id = current_user.user.user_id

    category_page_query_result = await TaskCategoryService.get_category_list_services(query_db, category_page_query, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=category_page_query_result)


@taskCategoryController.post('', dependencies=[Depends(CheckUserInterfaceAuth('todo:task:category:add'))])
@ValidateFields(validate_model='add_category')
@Log(title='任务分类', business_type=BusinessType.INSERT)
async def add_category(
    request: Request,
    add_category: TaskCategoryModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    添加分类
    """
    add_category.create_by = current_user.user.user_name
    add_category.create_time = datetime.now()
    add_category.update_by = current_user.user.user_name
    add_category.update_time = datetime.now()
    add_category.user_id = current_user.user.user_id
    add_category_result = await TaskCategoryService.add_category_services(query_db, add_category)
    logger.info(add_category_result.message)

    return ResponseUtil.success(msg=add_category_result.message)


@taskCategoryController.put('', dependencies=[Depends(CheckUserInterfaceAuth('todo:task:category:edit'))])
@ValidateFields(validate_model='edit_category')
@Log(title='任务分类', business_type=BusinessType.UPDATE)
async def edit_category(
    request: Request,
    edit_category: TaskCategoryModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    编辑分类
    """
    edit_category.update_by = current_user.user.user_name
    edit_category.update_time = datetime.now()
    edit_category_result = await TaskCategoryService.edit_category_services(query_db, edit_category)
    logger.info(edit_category_result.message)

    return ResponseUtil.success(msg=edit_category_result.message)


@taskCategoryController.delete('/{category_id}', dependencies=[Depends(CheckUserInterfaceAuth('todo:task:category:remove'))])
@Log(title='任务分类', business_type=BusinessType.DELETE)
async def delete_category(request: Request, category_id: int, query_db: AsyncSession = Depends(get_db)):
    """
    删除分类
    """
    delete_category = TaskCategoryModel(categoryId=category_id)
    delete_category_result = await TaskCategoryService.delete_category_services(query_db, delete_category)
    logger.info(delete_category_result.message)

    return ResponseUtil.success(msg=delete_category_result.message)
