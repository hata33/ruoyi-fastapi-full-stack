from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from config.constant import CommonConstant
from exceptions.exception import ServiceException
from module_todo.dao.note_dao import NoteDao
from module_todo.entity.vo.common_vo import CrudResponseModel
from module_todo.entity.vo.note_vo import DeleteNoteModel, NoteModel, NotePageQueryModel
from utils.common_util import CamelCaseUtil


class NoteService:
    """
    记事管理模块服务层
    """

    @classmethod
    async def get_note_list_services(
        cls, query_db: AsyncSession, query_object: NotePageQueryModel, is_page: bool = True
    ):
        """
        获取记事列表信息service
        """
        note_list_result = await NoteDao.get_note_list(query_db, query_object, is_page)
        return note_list_result

    @classmethod
    async def add_note_services(cls, query_db: AsyncSession, page_object: NoteModel):
        """
        新增记事信息service
        """
        try:
            await NoteDao.add_note_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_note_services(cls, query_db: AsyncSession, page_object: NoteModel):
        """
        编辑记事信息service
        """
        edit_note = page_object.model_dump(exclude_unset=True)
        note_info = await cls.note_detail_services(query_db, page_object.note_id)
        if note_info.note_id:
            try:
                await NoteDao.edit_note_dao(query_db, edit_note)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='记事不存在')

    @classmethod
    async def delete_note_services(cls, query_db: AsyncSession, page_object: DeleteNoteModel):
        """
        删除记事信息service
        """
        if page_object.note_ids:
            note_id_list = page_object.note_ids.split(',')
            try:
                for note_id in note_id_list:
                    await NoteDao.delete_note_dao(query_db, NoteModel(noteId=note_id))
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入记事id为空')

    @classmethod
    async def note_detail_services(cls, query_db: AsyncSession, note_id: int):
        """
        获取记事详细信息service
        """
        note = await NoteDao.get_note_detail_by_id(query_db, note_id=note_id)
        if note:
            result = NoteModel(**CamelCaseUtil.transform_result(note))
        else:
            result = NoteModel(**dict())
        return result
