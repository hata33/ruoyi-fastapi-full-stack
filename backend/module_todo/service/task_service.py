from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from config.constant import CommonConstant
from exceptions.exception import ServiceException
from module_todo.dao.task_dao import TaskDao
from module_todo.entity.vo.common_vo import CrudResponseModel
from module_todo.entity.vo.task_vo import DeleteTaskModel, TaskModel, TaskPageQueryModel
from utils.common_util import CamelCaseUtil


class TaskService:
    """
    任务管理模块服务层
    """

    @classmethod
    async def get_task_list_services(
        cls, query_db: AsyncSession, query_object: TaskPageQueryModel, is_page: bool = True
    ):
        """
        获取任务列表信息service
        """
        task_list_result = await TaskDao.get_task_list(query_db, query_object, is_page)
        return task_list_result

    @classmethod
    async def add_task_services(cls, query_db: AsyncSession, page_object: TaskModel):
        """
        新增任务信息service
        """
        try:
            await TaskDao.add_task_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_task_services(cls, query_db: AsyncSession, page_object: TaskModel):
        """
        编辑任务信息service
        """
        edit_task = page_object.model_dump(exclude_unset=True)
        task_info = await cls.task_detail_services(query_db, page_object.task_id)
        if task_info.task_id:
            try:
                await TaskDao.edit_task_dao(query_db, edit_task)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='任务不存在')

    @classmethod
    async def delete_task_services(cls, query_db: AsyncSession, page_object: DeleteTaskModel):
        """
        删除任务信息service
        """
        if page_object.task_ids:
            task_id_list = page_object.task_ids.split(',')
            try:
                for task_id in task_id_list:
                    await TaskDao.delete_task_dao(query_db, TaskModel(taskId=task_id))
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入任务id为空')

    @classmethod
    async def update_task_status_services(cls, query_db: AsyncSession, task_id: int, status: str):
        """
        更新任务状态service
        """
        task_info = await cls.task_detail_services(query_db, task_id)
        if not task_info.task_id:
            raise ServiceException(message='任务不存在')

        completed_at = datetime.now() if status == '1' else None
        try:
            await TaskDao.update_task_status_dao(query_db, task_id, status, completed_at)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='状态更新成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def task_detail_services(cls, query_db: AsyncSession, task_id: int):
        """
        获取任务详细信息service
        """
        task = await TaskDao.get_task_detail_by_id(query_db, task_id=task_id)
        if task:
            result = TaskModel(**CamelCaseUtil.transform_result(task))
        else:
            result = TaskModel(**dict())
        return result
