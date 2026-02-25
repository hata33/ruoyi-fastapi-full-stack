from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_todo.entity.do.task_category_do import SysTaskCategory
from module_todo.entity.vo.task_category_vo import TaskCategoryModel, TaskCategoryPageQueryModel
from utils.page_util import PageUtil


class TaskCategoryDao:
    """
    任务分类管理模块数据库操作层
    """

    @classmethod
    async def get_category_detail_by_id(cls, db: AsyncSession, category_id: int):
        """
        根据分类id获取分类详细信息
        """
        category_info = (await db.execute(select(SysTaskCategory).where(SysTaskCategory.category_id == category_id))).scalars().first()
        return category_info

    @classmethod
    async def get_category_list(cls, db: AsyncSession, query_object: TaskCategoryPageQueryModel, is_page: bool = False):
        """
        根据查询参数获取分类列表信息
        """
        query = (
            select(SysTaskCategory)
            .where(
                SysTaskCategory.category_name.like(f'%{query_object.category_name}%') if query_object.category_name else True,
                SysTaskCategory.user_id == query_object.user_id if query_object.user_id else True,
            )
            .order_by(SysTaskCategory.sort_order, SysTaskCategory.category_id)
            .distinct()
        )
        category_list = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)
        return category_list

    @classmethod
    async def add_category_dao(cls, db: AsyncSession, category: TaskCategoryModel):
        """
        新增分类数据库操作
        """
        db_category = SysTaskCategory(**category.model_dump())
        db.add(db_category)
        await db.flush()
        return db_category

    @classmethod
    async def edit_category_dao(cls, db: AsyncSession, category: dict):
        """
        编辑分类数据库操作
        """
        await db.execute(update(SysTaskCategory), [category])

    @classmethod
    async def delete_category_dao(cls, db: AsyncSession, category: TaskCategoryModel):
        """
        删除分类数据库操作
        """
        await db.execute(delete(SysTaskCategory).where(SysTaskCategory.category_id.in_([category.category_id])))
