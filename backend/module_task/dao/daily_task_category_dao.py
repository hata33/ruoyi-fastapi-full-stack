from datetime import datetime, time
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_task.entity.do.daily_task_category_do import DailyTaskCategoryDO
from module_task.entity.vo.daily_task_category_vo import (
    DailyTaskCategoryModel,
    DailyTaskCategoryPageQueryModel,
)
from utils.page_util import PageUtil


class DailyTaskCategoryDao:
    """
    每日任务分类管理模块数据库操作层
    用于组织和管理不同类型的每日任务
    """

    @classmethod
    async def get_category_detail_by_id(cls, db: AsyncSession, category_id: int):
        """
        根据分类id获取分类详细信息

        :param db: 异步数据库会话
        :param category_id: 分类ID
        :return: 分类详情对象
        """
        category_info = (
            await db.execute(
                select(DailyTaskCategoryDO).where(
                    DailyTaskCategoryDO.category_id == category_id
                )
            )
        ).scalars().first()
        return category_info

    @classmethod
    async def get_category_detail_by_info(cls, db: AsyncSession, category_name: str, user_id: int):
        """
        根据分类名称和用户ID获取分类详细信息
        用于校验分类名称唯一性

        :param db: 异步数据库会话
        :param category_name: 分类名称
        :param user_id: 用户ID
        :return: 分类详情对象
        """
        category_info = (
            await db.execute(
                select(DailyTaskCategoryDO).where(
                    DailyTaskCategoryDO.category_name == category_name,
                    DailyTaskCategoryDO.user_id == user_id
                )
            )
        ).scalars().first()
        return category_info

    @classmethod
    async def get_category_task_count(cls, db: AsyncSession, category_id: int) -> int:
        """
        获取分类下的任务数量
        用于删除分类前的校验

        :param db: 异步数据库会话
        :param category_id: 分类ID
        :return: 任务数量
        """
        from module_task.entity.do.daily_task_do import DailyTaskDO
        result = await db.execute(
            select(DailyTaskDO).where(
                DailyTaskDO.category_id == category_id
            )
        )
        return len(result.all())

    @classmethod
    async def get_category_list(
        cls,
        db: AsyncSession,
        query_object: DailyTaskCategoryPageQueryModel,
        is_page: bool = False,
    ):
        """
        根据查询参数获取分类列表信息
        支持按用户、分类名称等维度查询
        支持时间范围查询和分页

        :param db: 异步数据库会话
        :param query_object: 查询参数对象
        :param is_page: 是否分页
        :return: 分类列表
        """
        query = (
            select(DailyTaskCategoryDO)
            .where(
                DailyTaskCategoryDO.category_name.like(
                    f'%{query_object.category_name}%'
                )
                if query_object.category_name
                else True,
                DailyTaskCategoryDO.category_icon == query_object.category_icon
                if query_object.category_icon
                else True,
                DailyTaskCategoryDO.user_id == query_object.user_id
                if query_object.user_id
                else True,
                DailyTaskCategoryDO.create_time.between(
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
            .order_by(DailyTaskCategoryDO.sort_order, DailyTaskCategoryDO.category_id)
            .distinct()
        )
        category_list = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return category_list

    @classmethod
    async def add_category_dao(cls, db: AsyncSession, category: DailyTaskCategoryModel):
        """
        新增分类数据库操作

        :param db: 异步数据库会话
        :param category: 分类模型对象
        :return: 创建的分类对象
        """
        db_category = DailyTaskCategoryDO(**category.model_dump())
        db.add(db_category)
        await db.flush()
        return db_category

    @classmethod
    async def edit_category_dao(cls, db: AsyncSession, category: dict):
        """
        编辑分类数据库操作
        支持批量更新

        :param db: 异步数据库会话
        :param category: 分类字典对象
        """
        await db.execute(update(DailyTaskCategoryDO), [category])

    @classmethod
    async def delete_category_dao(cls, db: AsyncSession, category: DailyTaskCategoryModel):
        """
        删除分类数据库操作
        支持批量删除

        :param db: 异步数据库会话
        :param category: 分类模型对象（包含要删除的分类ID）
        """
        await db.execute(
            delete(DailyTaskCategoryDO).where(
                DailyTaskCategoryDO.category_id.in_([category.category_id])
            )
        )

    @classmethod
    async def batch_update_sort_order_dao(
        cls, db: AsyncSession, categories: list[dict]
    ):
        """
        批量更新分类排序
        用于拖拽排序功能

        :param db: 异步数据库会话
        :param categories: 分类列表，包含category_id和sort_order
        """
        if categories:
            await db.execute(update(DailyTaskCategoryDO), categories)

    @classmethod
    async def get_max_sort_order(cls, db: AsyncSession, user_id: int) -> int:
        """
        获取用户分类的最大排序值
        用于新分类默认排序

        :param db: 异步数据库会话
        :param user_id: 用户ID
        :return: 最大排序值
        """
        result = await db.execute(
            select(DailyTaskCategoryDO.sort_order)
            .where(DailyTaskCategoryDO.user_id == user_id)
            .order_by(DailyTaskCategoryDO.sort_order.desc())
            .limit(1)
        )
        max_sort = result.scalar()
        return max_sort if max_sort is not None else 0

    @classmethod
    async def count_categories_by_user(cls, db: AsyncSession, user_id: int) -> int:
        """
        统计用户的分类数量

        :param db: 异步数据库会话
        :param user_id: 用户ID
        :return: 分类数量
        """
        query = select(DailyTaskCategoryDO).where(
            DailyTaskCategoryDO.user_id == user_id
        )
        result = await db.execute(query)
        return len(result.all())

    @classmethod
    async def get_categories_by_user(cls, db: AsyncSession, user_id: int):
        """
        获取用户的所有分类
        按排序顺序返回

        :param db: 异步数据库会话
        :param user_id: 用户ID
        :return: 分类列表
        """
        query = (
            select(DailyTaskCategoryDO)
            .where(DailyTaskCategoryDO.user_id == user_id)
            .order_by(DailyTaskCategoryDO.sort_order, DailyTaskCategoryDO.category_id)
        )
        result = await db.execute(query)
        return result.scalars().all()
