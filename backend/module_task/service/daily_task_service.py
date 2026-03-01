from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from exceptions.exception import ServiceException
from module_task.dao.daily_task_dao import DailyTaskDao
from module_task.entity.vo.common_vo import CrudResponseModel
from module_task.entity.vo.daily_task_vo import (
    DeleteDailyTaskModel,
    DailyTaskModel,
    DailyTaskPageQueryModel,
    DailyTaskPinModel,
    DailyTaskReorderModel,
)
from utils.log_util import logger
from utils.common_util import CamelCaseUtil


class DailyTaskService:
    """
    每日任务管理模块服务层
    """

    @classmethod
    async def get_task_list_services(
        cls, query_db: AsyncSession, query_object: DailyTaskPageQueryModel, is_page: bool = True
    ):
        """
        获取任务列表信息service
        """
        logger.info(f'获取每日任务列表, 查询参数: {query_object.model_dump(exclude_unset=True)}')
        task_list_result = await DailyTaskDao.get_task_list(query_db, query_object, is_page)
        return task_list_result

    @classmethod
    async def task_detail_services(cls, query_db: AsyncSession, task_id: int):
        """
        获取任务详细信息service
        """
        logger.info(f'获取每日任务详情, task_id: {task_id}')
        task = await DailyTaskDao.get_task_detail_by_id(query_db, task_id=task_id)
        if task:
            result = DailyTaskModel(**CamelCaseUtil.transform_result(task))
            logger.info(f'获取每日任务详情成功, task_id: {task_id}')
        else:
            result = DailyTaskModel(**dict())
            logger.warning(f'每日任务不存在, task_id: {task_id}')
        return result

    @classmethod
    async def add_task_services(cls, query_db: AsyncSession, page_object: DailyTaskModel):
        """
        新增任务信息service
        """
        logger.info(f'新增每日任务, 标题: {page_object.title}')
        try:
            await DailyTaskDao.add_task_dao(query_db, page_object)
            await query_db.commit()
            logger.info(f'新增每日任务成功, 标题: {page_object.title}')
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'新增每日任务失败: {str(e)}')
            raise e

    @classmethod
    async def edit_task_services(cls, query_db: AsyncSession, page_object: DailyTaskModel):
        """
        编辑任务信息service
        """
        logger.info(f'编辑每日任务, task_id: {page_object.task_id}')
        edit_task = page_object.model_dump(exclude_unset=True)
        task_info = await cls.task_detail_services(query_db, page_object.task_id)
        if task_info.task_id:
            try:
                await DailyTaskDao.edit_task_dao(query_db, edit_task)
                await query_db.commit()
                logger.info(f'编辑每日任务成功, task_id: {page_object.task_id}')
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                logger.error(f'编辑每日任务失败: {str(e)}')
                raise e
        else:
            logger.warning(f'每日任务不存在, task_id: {page_object.task_id}')
            raise ServiceException(message='任务不存在')

    @classmethod
    async def delete_task_services(cls, query_db: AsyncSession, page_object: DeleteDailyTaskModel):
        """
        删除任务信息service
        """
        logger.info(f'删除每日任务, task_ids: {page_object.task_ids}')
        if page_object.task_ids:
            task_id_list = page_object.task_ids.split(',')
            try:
                for task_id in task_id_list:
                    await DailyTaskDao.delete_task_dao(query_db, DailyTaskModel(taskId=int(task_id)))
                await query_db.commit()
                logger.info(f'删除每日任务成功, task_ids: {page_object.task_ids}')
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                logger.error(f'删除每日任务失败: {str(e)}')
                raise e
        else:
            logger.error('传入任务id为空')
            raise ServiceException(message='传入任务id为空')

    @classmethod
    async def update_task_status_services(
        cls, query_db: AsyncSession, task_id: int, status: str
    ):
        """
        更新任务状态service（完成/重开）
        """
        logger.info(f'更新每日任务状态, task_id: {task_id}, status: {status}')
        task_info = await cls.task_detail_services(query_db, task_id)
        if not task_info.task_id:
            logger.warning(f'每日任务不存在, task_id: {task_id}')
            raise ServiceException(message='任务不存在')

        # 根据状态设置相关字段
        update_data = {'status': status}
        if status == 'completed':
            update_data['lastCompletedAt'] = datetime.now()
            update_data['completionCount'] = (task_info.completion_count or 0) + 1
        elif status == 'pending':
            # 重开时保留完成次数记录
            pass

        try:
            await DailyTaskDao.update_task_status_dao(query_db, task_id, update_data)
            await query_db.commit()
            logger.info(f'更新每日任务状态成功, task_id: {task_id}, status: {status}')
            message = '任务已完成' if status == 'completed' else '任务已重开'
            return CrudResponseModel(is_success=True, message=message)
        except Exception as e:
            await query_db.rollback()
            logger.error(f'更新每日任务状态失败: {str(e)}')
            raise e

    @classmethod
    async def toggle_task_disabled_services(
        cls, query_db: AsyncSession, task_id: int, disabled: bool
    ):
        """
        切换任务禁用状态service
        """
        logger.info(f'切换每日任务禁用状态, task_id: {task_id}, disabled: {disabled}')
        task_info = await cls.task_detail_services(query_db, task_id)
        if not task_info.task_id:
            logger.warning(f'每日任务不存在, task_id: {task_id}')
            raise ServiceException(message='任务不存在')

        status = 'disabled' if disabled else 'pending'
        update_data = {
            'status': status,
            'disabledAt': datetime.now() if disabled else None
        }

        try:
            await DailyTaskDao.update_task_status_dao(query_db, task_id, update_data)
            await query_db.commit()
            message = '任务已禁用' if disabled else '任务已启用'
            logger.info(f'切换每日任务禁用状态成功, task_id: {task_id}, disabled: {disabled}')
            return CrudResponseModel(is_success=True, message=message)
        except Exception as e:
            await query_db.rollback()
            logger.error(f'切换每日任务禁用状态失败: {str(e)}')
            raise e

    @classmethod
    async def reorder_tasks_services(
        cls, query_db: AsyncSession, page_object: DailyTaskReorderModel
    ):
        """
        批量排序任务service
        """
        logger.info(f'批量排序每日任务, 任务数量: {len(page_object.tasks)}')
        try:
            for task_data in page_object.tasks:
                task_id = task_data.get('task_id')
                sort_order = task_data.get('sort_order')
                if task_id is not None and sort_order is not None:
                    await DailyTaskDao.update_task_sort_order_dao(
                        query_db, task_id, sort_order
                    )
            await query_db.commit()
            logger.info(f'批量排序每日任务成功, 任务数量: {len(page_object.tasks)}')
            return CrudResponseModel(is_success=True, message='排序成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'批量排序每日任务失败: {str(e)}')
            raise e

    @classmethod
    async def toggle_pin_services(
        cls, query_db: AsyncSession, task_id: int, page_object: DailyTaskPinModel
    ):
        """
        置顶/取消置顶任务service
        """
        logger.info(f'切换每日任务置顶状态, task_id: {task_id}, is_pinned: {page_object.is_pinned}')
        task_info = await cls.task_detail_services(query_db, task_id)
        if not task_info.task_id:
            logger.warning(f'每日任务不存在, task_id: {task_id}')
            raise ServiceException(message='任务不存在')

        try:
            await DailyTaskDao.update_task_pin_dao(
                query_db, task_id, page_object.is_pinned
            )
            await query_db.commit()
            message = '任务已置顶' if page_object.is_pinned else '任务已取消置顶'
            logger.info(f'切换每日任务置顶状态成功, task_id: {task_id}, is_pinned: {page_object.is_pinned}')
            return CrudResponseModel(is_success=True, message=message)
        except Exception as e:
            await query_db.rollback()
            logger.error(f'切换每日任务置顶状态失败: {str(e)}')
            raise e

    @classmethod
    async def refresh_daily_tasks_services(cls, query_db: AsyncSession):
        """
        刷新每日任务service（定时任务调用）
        将所有 daily 类型且状态为 completed 的任务重置为 pending
        保留 completion_count 统计，忽略 disabled 状态的任务
        """
        logger.info('开始刷新每日任务')
        try:
            affected_count = await DailyTaskDao.refresh_daily_tasks_dao(query_db)
            await query_db.commit()
            logger.info(f'刷新每日任务成功, 影响行数: {affected_count}')
            return CrudResponseModel(
                is_success=True,
                message=f'刷新成功，共重置 {affected_count} 个任务'
            )
        except Exception as e:
            await query_db.rollback()
            logger.error(f'刷新每日任务失败: {str(e)}')
            raise e
