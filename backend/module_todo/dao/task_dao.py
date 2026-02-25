from datetime import datetime, time
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_todo.entity.do.task_do import SysTask
from module_todo.entity.vo.task_vo import TaskModel, TaskPageQueryModel
from utils.page_util import PageUtil


class TaskDao:
    """
    任务管理模块数据库操作层
    """

    @classmethod
    async def get_task_detail_by_id(cls, db: AsyncSession, task_id: int):
        """
        根据任务id获取任务详细信息
        """
        task_info = (await db.execute(select(SysTask).where(SysTask.task_id == task_id))).scalars().first()
        return task_info

    @classmethod
    async def get_task_list(cls, db: AsyncSession, query_object: TaskPageQueryModel, is_page: bool = False):
        """
        根据查询参数获取任务列表信息
        """
        query = (
            select(SysTask)
            .where(
                SysTask.task_title.like(f'%{query_object.task_title}%') if query_object.task_title else True,
                SysTask.status == query_object.status if query_object.status else True,
                SysTask.task_type == query_object.task_type if query_object.task_type else True,
                SysTask.priority == query_object.priority if query_object.priority else True,
                SysTask.user_id == query_object.user_id if query_object.user_id else True,
                SysTask.create_time.between(
                    datetime.combine(datetime.strptime(query_object.begin_time, '%Y-%m-%d'), time(00, 00, 00)),
                    datetime.combine(datetime.strptime(query_object.end_time, '%Y-%m-%d'), time(23, 59, 59)),
                )
                if query_object.begin_time and query_object.end_time
                else True,
            )
            .order_by(SysTask.task_id)
            .distinct()
        )
        task_list = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)
        return task_list

    @classmethod
    async def add_task_dao(cls, db: AsyncSession, task: TaskModel):
        """
        新增任务数据库操作
        """
        db_task = SysTask(**task.model_dump())
        db.add(db_task)
        await db.flush()
        return db_task

    @classmethod
    async def edit_task_dao(cls, db: AsyncSession, task: dict):
        """
        编辑任务数据库操作
        """
        await db.execute(update(SysTask), [task])

    @classmethod
    async def delete_task_dao(cls, db: AsyncSession, task: TaskModel):
        """
        删除任务数据库操作
        """
        await db.execute(delete(SysTask).where(SysTask.task_id.in_([task.task_id])))

    @classmethod
    async def update_task_status_dao(cls, db: AsyncSession, task_id: int, status: str, completed_at: datetime = None):
        """
        更新任务状态
        """
        update_data = {'status': status}
        if completed_at:
            update_data['completedAt'] = completed_at
        await db.execute(update(SysTask).where(SysTask.task_id == task_id), [update_data])
