from sqlalchemy.ext.asyncio import AsyncSession
from config.constant import CommonConstant
from exceptions.exception import ServiceException
from module_todo.dao.note_category_dao import NoteCategoryDao
from module_todo.entity.vo.common_vo import CrudResponseModel
from module_todo.entity.vo.note_category_vo import NoteCategoryModel, NoteCategoryPageQueryModel
from utils.common_util import CamelCaseUtil


class NoteCategoryService:
    """
    记事分类管理模块服务层
    """

    @classmethod
    async def get_category_list_services(
        cls, query_db: AsyncSession, query_object: NoteCategoryPageQueryModel, is_page: bool = True
    ):
        """
        获取分类列表信息service
        """
        category_list_result = await NoteCategoryDao.get_category_list(query_db, query_object, is_page)
        return category_list_result

    @classmethod
    async def check_category_unique_services(cls, query_db: AsyncSession, page_object: NoteCategoryModel):
        """
        校验分类是否存在service
        """
        category_id = -1 if page_object.category_id is None else page_object.category_id
        category = await NoteCategoryDao.get_category_detail_by_id(query_db, category_id)
        if category and category.category_id != category_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_category_services(cls, query_db: AsyncSession, page_object: NoteCategoryModel):
        """
        新增分类信息service
        """
        try:
            await NoteCategoryDao.add_category_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_category_services(cls, query_db: AsyncSession, page_object: NoteCategoryModel):
        """
        编辑分类信息service
        """
        edit_category = page_object.model_dump(exclude_unset=True)
        category_info = await cls.category_detail_services(query_db, page_object.category_id)
        if category_info.category_id:
            try:
                await NoteCategoryDao.edit_category_dao(query_db, edit_category)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='分类不存在')

    @classmethod
    async def delete_category_services(cls, query_db: AsyncSession, page_object: NoteCategoryModel):
        """
        删除分类信息service
        """
        try:
            await NoteCategoryDao.delete_category_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def category_detail_services(cls, query_db: AsyncSession, category_id: int):
        """
        获取分类详细信息service
        """
        category = await NoteCategoryDao.get_category_detail_by_id(query_db, category_id=category_id)
        if category:
            result = NoteCategoryModel(**CamelCaseUtil.transform_result(category))
        else:
            result = NoteCategoryModel(**dict())
        return result
