"""
聊天文件上传 DAO（Data Access Object）

说明：
- 负责文件上传相关的数据库操作
- 只处理数据访问，不包含业务逻辑
"""

from datetime import datetime, time
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from module_chat.entity.do.chat_file_do import ChatFile
from module_chat.entity.vo.chat_file_vo import ChatFileModel, ChatFilePageQueryModel
from utils.page_util import PageUtil


class ChatFileDao:
    """
    聊天文件上传模块数据库操作层
    """

    @classmethod
    async def get_file_by_id(cls, db: AsyncSession, file_id: int):
        """
        根据文件id获取文件详细信息

        :param db: orm对象
        :param file_id: 文件id
        :return: 文件信息对象
        """
        file_info = (await db.execute(select(ChatFile).where(ChatFile.file_id == file_id))).scalars().first()
        return file_info

    @classmethod
    async def get_file_list(cls, db: AsyncSession, query_object: ChatFilePageQueryModel, is_page: bool = False):
        """
        根据查询参数获取文件列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否分页
        :return: 文件列表信息对象
        """
        query = (
            select(ChatFile)
            .where(
                ChatFile.user_id == query_object.user_id if query_object.user_id else True,
                ChatFile.file_type == query_object.file_type if query_object.file_type else True,
                ChatFile.conversation_id == query_object.conversation_id if query_object.conversation_id else True,
            )
            .order_by(ChatFile.file_id.desc())
            .distinct()
        )
        file_list = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)
        return file_list

    @classmethod
    async def add_file(cls, db: AsyncSession, file: ChatFileModel):
        """
        新增文件

        :param db: orm对象
        :param file: 文件对象
        :return: 文件对象
        """
        db_file = ChatFile(**file.model_dump())
        db.add(db_file)
        await db.flush()
        return db_file

    @classmethod
    async def delete_file(cls, db: AsyncSession, file_ids: list):
        """
        删除文件

        :param db: orm对象
        :param file_ids: 文件ID列表
        :return:
        """
        await db.execute(delete(ChatFile).where(ChatFile.file_id.in_(file_ids)))

    @classmethod
    async def update_file_conversation(cls, db: AsyncSession, file_id: int, conversation_id: int):
        """
        更新文件关联会话

        :param db: orm对象
        :param file_id: 文件ID
        :param conversation_id: 会话ID
        :return:
        """
        from sqlalchemy import update

        await db.execute(
            update(ChatFile).where(ChatFile.file_id == file_id).values(conversation_id=conversation_id)
        )

    @classmethod
    async def update_file_message(cls, db: AsyncSession, file_id: int, message_id: int):
        """
        更新文件关联消息

        :param db: orm对象
        :param file_id: 文件ID
        :param message_id: 消息ID
        :return:
        """
        from sqlalchemy import update

        await db.execute(update(ChatFile).where(ChatFile.file_id == file_id).values(message_id=message_id))
