"""
任务控制器模块
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
from module_todo.entity.vo.task_vo import DeleteTaskModel, TaskModel, TaskPageQueryModel, TaskStatusModel
from module_todo.service.task_service import TaskService
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


taskController = APIRouter(prefix='/todo/task', dependencies=[Depends(LoginService.get_current_user)])


@taskController.get(
    '/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('todo:task:list'))]
)
async def get_task_list(
    request: Request,
    task_page_query: TaskPageQueryModel = Depends(TaskPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
):
    """
    获取任务列表（分页）
    """
    # 设置当前用户ID过滤
    current_user: CurrentUserModel = await LoginService.get_current_user(request)
    task_page_query.user_id = current_user.user.user_id

    task_page_query_result = await TaskService.get_task_list_services(query_db, task_page_query, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=task_page_query_result)


@taskController.get(
    '/todo', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('todo:task:list'))]
)
async def get_todo_list(
    request: Request,
    task_page_query: TaskPageQueryModel = Depends(TaskPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
):
    """
    获取Todo列表（Task的快捷入口，task_type=2）
    """
    # 设置当前用户ID过滤和类型过滤
    current_user: CurrentUserModel = await LoginService.get_current_user(request)
    task_page_query.user_id = current_user.user.user_id
    task_page_query.task_type = '2'  # Todo类型

    task_page_query_result = await TaskService.get_task_list_services(query_db, task_page_query, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=task_page_query_result)


@taskController.get(
    '/{task_id}', response_model=TaskModel, dependencies=[Depends(CheckUserInterfaceAuth('todo:task:query'))]
)
async def query_task_detail(request: Request, task_id: int, query_db: AsyncSession = Depends(get_db)):
    """
    获取任务详细信息
    """
    task_detail_result = await TaskService.task_detail_services(query_db, task_id)
    logger.info(f'获取task_id为{task_id}的信息成功')

    return ResponseUtil.success(data=task_detail_result)


@taskController.post('', dependencies=[Depends(CheckUserInterfaceAuth('todo:task:add'))])
@ValidateFields(validate_model='add_task')
@Log(title='任务管理', business_type=BusinessType.INSERT)
async def add_task(
    request: Request,
    add_task: TaskModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    添加任务
    """
    add_task.create_by = current_user.user.user_name
    add_task.create_time = datetime.now()
    add_task.update_by = current_user.user.user_name
    add_task.update_time = datetime.now()
    add_task.user_id = current_user.user.user_id
    add_task_result = await TaskService.add_task_services(query_db, add_task)
    logger.info(add_task_result.message)

    return ResponseUtil.success(msg=add_task_result.message)


@taskController.put('', dependencies=[Depends(CheckUserInterfaceAuth('todo:task:edit'))])
@ValidateFields(validate_model='edit_task')
@Log(title='任务管理', business_type=BusinessType.UPDATE)
async def edit_task(
    request: Request,
    edit_task: TaskModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    编辑任务
    """
    edit_task.update_by = current_user.user.user_name
    edit_task.update_time = datetime.now()
    edit_task_result = await TaskService.edit_task_services(query_db, edit_task)
    logger.info(edit_task_result.message)

    return ResponseUtil.success(msg=edit_task_result.message)


@taskController.delete('/{task_ids}', dependencies=[Depends(CheckUserInterfaceAuth('todo:task:remove'))])
@Log(title='任务管理', business_type=BusinessType.DELETE)
async def delete_task(request: Request, task_ids: str, query_db: AsyncSession = Depends(get_db)):
    """
    删除任务
    """
    delete_task = DeleteTaskModel(taskIds=task_ids)
    delete_task_result = await TaskService.delete_task_services(query_db, delete_task)
    logger.info(delete_task_result.message)

    return ResponseUtil.success(msg=delete_task_result.message)


@taskController.patch('/{task_id}/complete', dependencies=[Depends(CheckUserInterfaceAuth('todo:task:edit'))])
@Log(title='任务管理', business_type=BusinessType.UPDATE)
async def complete_task(request: Request, task_id: int, query_db: AsyncSession = Depends(get_db)):
    """
    完成任务
    """
    complete_task_result = await TaskService.update_task_status_services(query_db, task_id, '1')
    logger.info(complete_task_result.message)

    return ResponseUtil.success(msg=complete_task_result.message)


@taskController.patch('/{task_id}/reopen', dependencies=[Depends(CheckUserInterfaceAuth('todo:task:edit'))])
@Log(title='任务管理', business_type=BusinessType.UPDATE)
async def reopen_task(request: Request, task_id: int, query_db: AsyncSession = Depends(get_db)):
    """
    重开任务
    """
    reopen_task_result = await TaskService.update_task_status_services(query_db, task_id, '0')
    logger.info(reopen_task_result.message)

    return ResponseUtil.success(msg=reopen_task_result.message)
