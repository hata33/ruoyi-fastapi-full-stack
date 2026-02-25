from datetime import datetime, time
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_todo.entity.do.note_do import SysNote
from module_todo.entity.vo.note_vo import NoteModel, NotePageQueryModel
from utils.page_util import PageUtil


class NoteDao:
    """
    记事管理模块数据库操作层
    """

    @classmethod
    async def get_note_detail_by_id(cls, db: AsyncSession, note_id: int):
        """
        根据记事id获取记事详细信息
        """
        note_info = (await db.execute(select(SysNote).where(SysNote.note_id == note_id))).scalars().first()
        return note_info

    @classmethod
    async def get_note_list(cls, db: AsyncSession, query_object: NotePageQueryModel, is_page: bool = False):
        """
        根据查询参数获取记事列表信息
        """
        query = (
            select(SysNote)
            .where(
                SysNote.note_title.like(f'%{query_object.note_title}%') if query_object.note_title else True,
                SysNote.status == query_object.status if query_object.status else True,
                SysNote.user_id == query_object.user_id if query_object.user_id else True,
                SysNote.create_time.between(
                    datetime.combine(datetime.strptime(query_object.begin_time, '%Y-%m-%d'), time(00, 00, 00)),
                    datetime.combine(datetime.strptime(query_object.end_time, '%Y-%m-%d'), time(23, 59, 59)),
                )
                if query_object.begin_time and query_object.end_time
                else True,
            )
            .order_by(SysNote.note_id)
            .distinct()
        )
        note_list = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)
        return note_list

    @classmethod
    async def add_note_dao(cls, db: AsyncSession, note: NoteModel):
        """
        新增记事数据库操作
        """
        db_note = SysNote(**note.model_dump())
        db.add(db_note)
        await db.flush()
        return db_note

    @classmethod
    async def edit_note_dao(cls, db: AsyncSession, note: dict):
        """
        编辑记事数据库操作
        """
        await db.execute(update(SysNote), [note])

    @classmethod
    async def delete_note_dao(cls, db: AsyncSession, note: NoteModel):
        """
        删除记事数据库操作
        """
        await db.execute(delete(SysNote).where(SysNote.note_id.in_([note.note_id])))
