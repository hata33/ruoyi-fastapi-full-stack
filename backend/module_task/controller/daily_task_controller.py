"""
每日任务控制器模块
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
from module_task.entity.vo.daily_task_vo import (
    DeleteDailyTaskModel,
    DailyTaskModel,
    DailyTaskPageQueryModel,
    DailyTaskPinModel,
    DailyTaskReorderModel,
)
from module_task.service.daily_task_service import DailyTaskService
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


dailyTaskController = APIRouter(
    prefix='/daily-task', dependencies=[Depends(LoginService.get_current_user)]
)


@dailyTaskController.get(
    '/list',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('daily:task:list'))],
)
async def get_daily_task_list(
    title: Optional[str] = None,
    taskType: Optional[str] = None,
    status: Optional[str] = None,
    isPinned: Optional[bool] = None,
    categoryId: Optional[int] = None,
    beginTime: Optional[str] = None,
    endTime: Optional[str] = None,
    pageNum: int = 1,
    pageSize: int = 10,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    获取每日任务列表（分页）
    """
    from module_task.entity.vo.daily_task_vo import DailyTaskPageQueryModel
    task_page_query = DailyTaskPageQueryModel(
        title=title,
        task_type=taskType,
        status=status,
        is_pinned=isPinned,
        category_id=categoryId,
        begin_time=beginTime,
        end_time=endTime,
        page_num=pageNum,
        page_size=pageSize,
    )

    # 设置当前用户ID过滤
    task_page_query.user_id = current_user.user.user_id

    task_page_query_result = await DailyTaskService.get_task_list_services(
        query_db, task_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=task_page_query_result)


@dailyTaskController.get(
    '/{task_id}',
    response_model=DailyTaskModel,
    dependencies=[Depends(CheckUserInterfaceAuth('daily:task:query'))],
)
async def query_daily_task_detail(task_id: int, query_db: AsyncSession = Depends(get_db)):
    """
    获取每日任务详细信息
    """
    task_detail_result = await DailyTaskService.task_detail_services(query_db, task_id)
    logger.info(f'获取task_id为{task_id}的信息成功')

    return ResponseUtil.success(data=task_detail_result)


@dailyTaskController.post('', dependencies=[Depends(CheckUserInterfaceAuth('daily:task:add'))])
@ValidateFields(validate_model='add_task')
@Log(title='每日任务管理', business_type=BusinessType.INSERT)
async def add_daily_task(
    request: Request,
    add_task: DailyTaskModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    添加每日任务
    """
    add_task.create_by = current_user.user.user_name
    add_task.create_time = datetime.now()
    add_task.update_by = current_user.user.user_name
    add_task.update_time = datetime.now()
    add_task.user_id = current_user.user.user_id
    add_task_result = await DailyTaskService.add_task_services(query_db, add_task)
    logger.info(add_task_result.message)

    return ResponseUtil.success(msg=add_task_result.message)


@dailyTaskController.put('', dependencies=[Depends(CheckUserInterfaceAuth('daily:task:edit'))])
@ValidateFields(validate_model='edit_task')
@Log(title='每日任务管理', business_type=BusinessType.UPDATE)
async def edit_daily_task(
    request: Request,
    edit_task: DailyTaskModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    编辑每日任务
    """
    edit_task.update_by = current_user.user.user_name
    edit_task.update_time = datetime.now()
    edit_task_result = await DailyTaskService.edit_task_services(query_db, edit_task)
    logger.info(edit_task_result.message)

    return ResponseUtil.success(msg=edit_task_result.message)


@dailyTaskController.delete(
    '/{task_ids}', dependencies=[Depends(CheckUserInterfaceAuth('daily:task:remove'))]
)
@Log(title='每日任务管理', business_type=BusinessType.DELETE)
async def delete_daily_task(
    request: Request,
    task_ids: str,
    query_db: AsyncSession = Depends(get_db)
):
    """
    删除每日任务
    """
    delete_task = DeleteDailyTaskModel(task_ids=task_ids)
    delete_task_result = await DailyTaskService.delete_task_services(query_db, delete_task)
    logger.info(delete_task_result.message)

    return ResponseUtil.success(msg=delete_task_result.message)


@dailyTaskController.patch(
    '/{task_id}/complete', dependencies=[Depends(CheckUserInterfaceAuth('daily:task:edit'))]
)
@Log(title='每日任务管理', business_type=BusinessType.UPDATE)
async def complete_daily_task(
    request: Request,
    task_id: int,
    query_db: AsyncSession = Depends(get_db)
):
    """
    完成每日任务
    """
    complete_task_result = await DailyTaskService.update_task_status_services(
        query_db, task_id, 'completed'
    )
    logger.info(complete_task_result.message)

    return ResponseUtil.success(msg=complete_task_result.message)


@dailyTaskController.patch(
    '/{task_id}/reopen', dependencies=[Depends(CheckUserInterfaceAuth('daily:task:edit'))]
)
@Log(title='每日任务管理', business_type=BusinessType.UPDATE)
async def reopen_daily_task(
    request: Request,
    task_id: int,
    query_db: AsyncSession = Depends(get_db)
):
    """
    重开每日任务
    """
    reopen_task_result = await DailyTaskService.update_task_status_services(
        query_db, task_id, 'pending'
    )
    logger.info(reopen_task_result.message)

    return ResponseUtil.success(msg=reopen_task_result.message)


@dailyTaskController.patch(
    '/{task_id}/disable', dependencies=[Depends(CheckUserInterfaceAuth('daily:task:edit'))]
)
@Log(title='每日任务管理', business_type=BusinessType.UPDATE)
async def disable_daily_task(
    request: Request,
    task_id: int,
    query_db: AsyncSession = Depends(get_db)
):
    """
    禁用每日任务
    """
    disable_task_result = await DailyTaskService.update_task_status_services(
        query_db, task_id, 'disabled'
    )
    logger.info(disable_task_result.message)

    return ResponseUtil.success(msg=disable_task_result.message)


@dailyTaskController.patch(
    '/{task_id}/enable', dependencies=[Depends(CheckUserInterfaceAuth('daily:task:edit'))]
)
@Log(title='每日任务管理', business_type=BusinessType.UPDATE)
async def enable_daily_task(
    request: Request,
    task_id: int,
    query_db: AsyncSession = Depends(get_db)
):
    """
    启用每日任务
    """
    enable_task_result = await DailyTaskService.update_task_status_services(
        query_db, task_id, 'pending'
    )
    logger.info(enable_task_result.message)

    return ResponseUtil.success(msg=enable_task_result.message)


@dailyTaskController.put(
    '/reorder', dependencies=[Depends(CheckUserInterfaceAuth('daily:task:edit'))]
)
@ValidateFields(validate_model='reorder_tasks')
@Log(title='每日任务管理', business_type=BusinessType.UPDATE)
async def reorder_daily_tasks(
    request: Request,
    reorder_data: DailyTaskReorderModel,
    query_db: AsyncSession = Depends(get_db),
):
    """
    批量排序每日任务
    """
    reorder_result = await DailyTaskService.reorder_tasks_services(query_db, reorder_data.tasks)
    logger.info(reorder_result.message)

    return ResponseUtil.success(msg=reorder_result.message)


@dailyTaskController.put(
    '/{task_id}/pin', dependencies=[Depends(CheckUserInterfaceAuth('daily:task:edit'))]
)
@ValidateFields(validate_model='pin_task')
@Log(title='每日任务管理', business_type=BusinessType.UPDATE)
async def pin_daily_task(
    request: Request,
    task_id: int,
    pin_data: DailyTaskPinModel,
    query_db: AsyncSession = Depends(get_db),
):
    """
    置顶/取消置顶每日任务
    """
    pin_result = await DailyTaskService.toggle_pin_services(query_db, task_id, pin_data)
    logger.info(pin_result.message)

    return ResponseUtil.success(msg=pin_result.message)
