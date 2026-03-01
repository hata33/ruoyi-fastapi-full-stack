from datetime import datetime, time
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_task.entity.do.daily_task_do import DailyTaskDO
from module_task.entity.vo.daily_task_vo import DailyTaskModel, DailyTaskPageQueryModel
from utils.page_util import PageUtil


class DailyTaskDao:
    """
    每日任务管理模块数据库操作层
    支持每日自动刷新、可勾选完成并自动置灰、自动累计完成次数、支持拖拽排序/置顶/置底、可设置禁用冻结
    """

    @classmethod
    async def get_task_detail_by_id(cls, db: AsyncSession, task_id: int):
        """
        根据任务id获取任务详细信息

        :param db: 异步数据库会话
        :param task_id: 任务ID
        :return: 任务详情对象
        """
        task_info = (
            await db.execute(
                select(DailyTaskDO).where(DailyTaskDO.task_id == task_id)
            )
        ).scalars().first()
        return task_info

    @classmethod
    async def get_task_list(
        cls, db: AsyncSession, query_object: DailyTaskPageQueryModel, is_page: bool = False
    ):
        """
        根据查询参数获取任务列表信息
        支持按用户、任务类型、状态、置顶状态等多维度查询
        支持时间范围查询和分页

        :param db: 异步数据库会话
        :param query_object: 查询参数对象
        :param is_page: 是否分页
        :return: 任务列表
        """
        query = (
            select(DailyTaskDO)
            .where(
                DailyTaskDO.title.like(f'%{query_object.title}%')
                if query_object.title
                else True,
                DailyTaskDO.task_type == query_object.task_type
                if query_object.task_type
                else True,
                DailyTaskDO.status == query_object.status
                if query_object.status
                else True,
                DailyTaskDO.is_pinned == query_object.is_pinned
                if query_object.is_pinned is not None
                else True,
                DailyTaskDO.user_id == query_object.user_id
                if query_object.user_id
                else True,
                DailyTaskDO.category_id == query_object.category_id
                if query_object.category_id
                else True,
                DailyTaskDO.icon_type == query_object.icon_type
                if query_object.icon_type
                else True,
                DailyTaskDO.create_time.between(
                    datetime.combine(
                        datetime.strptime(query_object.begin_time, '%Y-%m-%d'),
                        time(00, 00, 00),
                    ),
                    datetime.combine(
                        datetime.strptime(query_object.end_time, '%Y-%m-%d'),
                        time(23, 59, 59),
                    ),
                )
                if query_object.begin_time and query_object.end_time
                else True,
            )
            .order_by(DailyTaskDO.is_pinned.desc(), DailyTaskDO.sort_order, DailyTaskDO.task_id)
            .distinct()
        )
        task_list = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return task_list

    @classmethod
    async def add_task_dao(cls, db: AsyncSession, task: DailyTaskModel):
        """
        新增任务数据库操作

        :param db: 异步数据库会话
        :param task: 任务模型对象
        :return: 创建的任务对象
        """
        db_task = DailyTaskDO(**task.model_dump())
        db.add(db_task)
        await db.flush()
        return db_task

    @classmethod
    async def edit_task_dao(cls, db: AsyncSession, task: dict):
        """
        编辑任务数据库操作
        支持批量更新

        :param db: 异步数据库会话
        :param task: 任务字典对象
        """
        await db.execute(update(DailyTaskDO), [task])

    @classmethod
    async def delete_task_dao(cls, db: AsyncSession, task: DailyTaskModel):
        """
        删除任务数据库操作
        支持批量删除

        :param db: 异步数据库会话
        :param task: 任务模型对象（包含要删除的任务ID）
        """
        await db.execute(
            delete(DailyTaskDO).where(DailyTaskDO.task_id.in_([task.task_id]))
        )

    @classmethod
    async def update_task_status_dao(
        cls,
        db: AsyncSession,
        task_id: int,
        status: str,
        completion_count: int = None,
        last_completed_at: datetime = None,
        disabled_at: datetime = None,
    ):
        """
        更新任务状态
        用于任务完成、重开、禁用、启用等操作

        :param db: 异步数据库会话
        :param task_id: 任务ID
        :param status: 新状态
        :param completion_count: 累计完成次数（可选）
        :param last_completed_at: 最后完成时间（可选）
        :param disabled_at: 禁用时间（可选）
        """
        update_data = {'status': status}
        if completion_count is not None:
            update_data['completion_count'] = completion_count
        if last_completed_at is not None:
            update_data['last_completed_at'] = last_completed_at
        if disabled_at is not None:
            update_data['disabled_at'] = disabled_at
        if status == 'pending':
            # 重新打开任务时，清除禁用时间
            update_data['disabled_at'] = None
        await db.execute(
            update(DailyTaskDO).where(DailyTaskDO.task_id == task_id), [update_data]
        )

    @classmethod
    async def update_task_pin_dao(cls, db: AsyncSession, task_id: int, is_pinned: bool):
        """
        更新任务置顶状态

        :param db: 异步数据库会话
        :param task_id: 任务ID
        :param is_pinned: 是否置顶
        """
        await db.execute(
            update(DailyTaskDO).where(DailyTaskDO.task_id == task_id),
            [{'task_id': task_id, 'is_pinned': is_pinned}],
        )

    @classmethod
    async def batch_update_sort_order_dao(cls, db: AsyncSession, tasks: list[dict]):
        """
        批量更新任务排序
        用于拖拽排序功能

        :param db: 异步数据库会话
        :param tasks: 任务列表，包含task_id和sort_order
        """
        if tasks:
            await db.execute(update(DailyTaskDO), tasks)

    @classmethod
    async def get_max_sort_order(cls, db: AsyncSession, user_id: int) -> int:
        """
        获取用户任务的最大排序值
        用于新任务默认排序

        :param db: 异步数据库会话
        :param user_id: 用户ID
        :return: 最大排序值
        """
        result = await db.execute(
            select(DailyTaskDO.sort_order)
            .where(DailyTaskDO.user_id == user_id)
            .order_by(DailyTaskDO.sort_order.desc())
            .limit(1)
        )
        max_sort = result.scalar()
        return max_sort if max_sort is not None else 0

    @classmethod
    async def get_daily_tasks_for_refresh(cls, db: AsyncSession):
        """
        获取所有需要刷新的每日任务
        用于定时任务在每日00:00刷新已完成的daily类型任务

        :param db: 异步数据库会话
        :return: 需要刷新的任务列表
        """
        query = (
            select(DailyTaskDO).where(
                DailyTaskDO.task_type == 'daily',
                DailyTaskDO.status == 'completed',
            )
        )
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def count_tasks_by_user_and_status(
        cls, db: AsyncSession, user_id: int, status: str = None
    ):
        """
        统计用户的任务数量
        可按状态筛选

        :param db: 异步数据库会话
        :param user_id: 用户ID
        :param status: 任务状态（可选）
        :return: 任务数量
        """
        query = select(DailyTaskDO).where(DailyTaskDO.user_id == user_id)
        if status:
            query = query.where(DailyTaskDO.status == status)
        result = await db.execute(query)
        return len(result.all())
