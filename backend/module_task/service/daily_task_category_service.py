from sqlalchemy.ext.asyncio import AsyncSession
from config.constant import CommonConstant
from exceptions.exception import ServiceException
from module_task.dao.daily_task_category_dao import DailyTaskCategoryDao
from module_task.entity.vo.common_vo import CrudResponseModel
from module_task.entity.vo.daily_task_category_vo import (
    DailyTaskCategoryModel,
    DailyTaskCategoryPageQueryModel,
)
from utils.log_util import logger
from utils.common_util import CamelCaseUtil


class DailyTaskCategoryService:
    """
    每日任务分类管理模块服务层
    """

    @classmethod
    async def get_category_list_services(
        cls, query_db: AsyncSession, query_object: DailyTaskCategoryPageQueryModel, is_page: bool = True
    ):
        """
        获取分类列表信息service
        """
        logger.info(f'获取每日任务分类列表, 查询参数: {query_object.model_dump(exclude_unset=True)}')
        category_list_result = await DailyTaskCategoryDao.get_category_list(query_db, query_object, is_page)
        return category_list_result

    @classmethod
    async def check_category_unique_services(cls, query_db: AsyncSession, page_object: DailyTaskCategoryModel):
        """
        校验分类是否存在service
        """
        category_id = -1 if page_object.category_id is None else page_object.category_id
        category = await DailyTaskCategoryDao.get_category_detail_by_info(
            query_db, page_object.category_name, page_object.user_id
        )
        if category and category.category_id != category_id:
            logger.warning(f'分类名称已存在, category_name: {page_object.category_name}')
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_category_services(cls, query_db: AsyncSession, page_object: DailyTaskCategoryModel):
        """
        新增分类信息service
        """
        logger.info(f'新增每日任务分类, 名称: {page_object.category_name}')
        try:
            # 校验分类名称唯一性
            await cls.check_category_unique_services(query_db, page_object)
            await DailyTaskCategoryDao.add_category_dao(query_db, page_object)
            await query_db.commit()
            logger.info(f'新增每日任务分类成功, 名称: {page_object.category_name}')
            return CrudResponseModel(is_success=True, message='新增成功')
        except ServiceException:
            await query_db.rollback()
            raise
        except Exception as e:
            await query_db.rollback()
            logger.error(f'新增每日任务分类失败: {str(e)}')
            raise e

    @classmethod
    async def edit_category_services(cls, query_db: AsyncSession, page_object: DailyTaskCategoryModel):
        """
        编辑分类信息service
        """
        logger.info(f'编辑每日任务分类, category_id: {page_object.category_id}')
        edit_category = page_object.model_dump(exclude_unset=True)
        category_info = await cls.category_detail_services(query_db, page_object.category_id)
        if category_info.category_id:
            try:
                # 校验分类名称唯一性
                await cls.check_category_unique_services(query_db, page_object)
                await DailyTaskCategoryDao.edit_category_dao(query_db, edit_category)
                await query_db.commit()
                logger.info(f'编辑每日任务分类成功, category_id: {page_object.category_id}')
                return CrudResponseModel(is_success=True, message='更新成功')
            except ServiceException:
                await query_db.rollback()
                raise
            except Exception as e:
                await query_db.rollback()
                logger.error(f'编辑每日任务分类失败: {str(e)}')
                raise e
        else:
            logger.warning(f'每日任务分类不存在, category_id: {page_object.category_id}')
            raise ServiceException(message='分类不存在')

    @classmethod
    async def delete_category_services(cls, query_db: AsyncSession, page_object: DailyTaskCategoryModel):
        """
        删除分类信息service
        """
        logger.info(f'删除每日任务分类, category_id: {page_object.category_id}')
        try:
            # 检查分类下是否有任务
            task_count = await DailyTaskCategoryDao.get_category_task_count(
                query_db, page_object.category_id
            )
            if task_count > 0:
                logger.warning(f'分类下存在任务，无法删除, category_id: {page_object.category_id}')
                raise ServiceException(message=f'分类下存在 {task_count} 个任务，无法删除')

            await DailyTaskCategoryDao.delete_category_dao(query_db, page_object)
            await query_db.commit()
            logger.info(f'删除每日任务分类成功, category_id: {page_object.category_id}')
            return CrudResponseModel(is_success=True, message='删除成功')
        except ServiceException:
            await query_db.rollback()
            raise
        except Exception as e:
            await query_db.rollback()
            logger.error(f'删除每日任务分类失败: {str(e)}')
            raise e

    @classmethod
    async def category_detail_services(cls, query_db: AsyncSession, category_id: int):
        """
        获取分类详细信息service
        """
        logger.info(f'获取每日任务分类详情, category_id: {category_id}')
        category = await DailyTaskCategoryDao.get_category_detail_by_id(query_db, category_id=category_id)
        if category:
            result = DailyTaskCategoryModel(**CamelCaseUtil.transform_result(category))
            logger.info(f'获取每日任务分类详情成功, category_id: {category_id}')
        else:
            result = DailyTaskCategoryModel(**dict())
            logger.warning(f'每日任务分类不存在, category_id: {category_id}')
        return result
