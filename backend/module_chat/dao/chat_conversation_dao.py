"""
聊天会话管理 DAO（Data Access Object）

说明：
- 负责会话相关的数据库操作
- 只处理数据访问，不包含业务逻辑
"""

from datetime import datetime, time
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_chat.entity.do.chat_conversation_do import ChatConversation
from module_chat.entity.do.chat_conversation_tag_do import ChatConversationTag
from module_chat.entity.vo.chat_conversation_vo import (
    ChatConversationModel,
    ChatConversationPageQueryModel,
)
from utils.page_util import PageUtil


class ChatConversationDao:
    """
    聊天会话管理模块数据库操作层
    """

    @classmethod
    async def get_conversation_by_id(cls, db: AsyncSession, conversation_id: str):
        """
        根据会话id获取会话详细信息

        :param db: orm对象
        :param conversation_id: 会话id
        :return: 会话信息对象
        """
        conversation_info = (
            await db.execute(
                select(ChatConversation).where(ChatConversation.conversation_id == conversation_id)
            )
        ).scalars().first()
        return conversation_info

    @classmethod
    async def get_conversation_list(cls, db: AsyncSession, query_object: ChatConversationPageQueryModel, is_page: bool = False):
        """
        根据查询参数获取会话列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否分页
        :return: 会话列表信息对象
        """
        query = (
            select(ChatConversation)
            .where(
                ChatConversation.user_id == query_object.user_id if query_object.user_id else True,
                ChatConversation.title.like(f'%{query_object.title}%') if query_object.title else True,
                ChatConversation.model_id == query_object.model_id if query_object.model_id else True,
                ChatConversation.is_pinned == query_object.is_pinned if query_object.is_pinned is not None else True,
                ChatConversation.create_time.between(
                    datetime.combine(datetime.strptime(query_object.begin_time, '%Y-%m-%d'), time(00, 00, 00)),
                    datetime.combine(datetime.strptime(query_object.end_time, '%Y-%m-%d'), time(23, 59, 59)),
                )
                if query_object.begin_time and query_object.end_time
                else True,
            )
            .order_by(ChatConversation.is_pinned.desc(), ChatConversation.pin_time.desc(), ChatConversation.update_time.desc())
            .distinct()
        )
        conversation_list = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)
        return conversation_list

    @classmethod
    async def add_conversation(cls, db: AsyncSession, conversation: ChatConversation):
        """
        新增会话数据库操作

        :param db: orm对象
        :param conversation: 会话对象（数据库实体）
        :return: 新增会话对象
        """
        db.add(conversation)
        await db.flush()
        return conversation

    @classmethod
    async def edit_conversation(cls, db: AsyncSession, conversation: dict):
        """
        编辑会话数据库操作

        :param db: orm对象
        :param conversation: 需要更新的会话字典
        :return:
        """
        await db.execute(update(ChatConversation), [conversation])

    @classmethod
    async def delete_conversation(cls, db: AsyncSession, conversation_ids: list):
        """
        删除会话数据库操作

        :param db: orm对象
        :param conversation_ids: 会话ID列表
        :return:
        """
        await db.execute(delete(ChatConversation).where(ChatConversation.conversation_id.in_(conversation_ids)))

    @classmethod
    async def update_conversation_pin(cls, db: AsyncSession, conversation_id: str, is_pinned: bool, pin_time: datetime = None):
        """
        更新会话置顶状态

        :param db: orm对象
        :param conversation_id: 会话ID
        :param is_pinned: 是否置顶
        :param pin_time: 置顶时间
        :return:
        """
        update_data = {'is_pinned': is_pinned}
        if is_pinned and pin_time:
            update_data['pin_time'] = pin_time
        else:
            update_data['pin_time'] = None

        await db.execute(
            update(ChatConversation)
            .where(ChatConversation.conversation_id == conversation_id)
            .values(**update_data)
            .execution_options(synchronize_session=False)
        )

    @classmethod
    async def update_conversation_message_count(cls, db: AsyncSession, conversation_id: str, delta: int = 1):
        """
        更新会话消息数量

        :param db: orm对象
        :param conversation_id: 会话ID
        :param delta: 增量
        :return:
        """
        await db.execute(
            update(ChatConversation)
            .where(ChatConversation.conversation_id == conversation_id)
            .values(message_count=ChatConversation.message_count + delta)
            .execution_options(synchronize_session=False)
        )

    @classmethod
    async def update_conversation_tokens(cls, db: AsyncSession, conversation_id: str, delta: int = 0):
        """
        更新会话累计token数

        :param db: orm对象
        :param conversation_id: 会话ID
        :param delta: 增量
        :return:
        """
        await db.execute(
            update(ChatConversation)
            .where(ChatConversation.conversation_id == conversation_id)
            .values(total_tokens=ChatConversation.total_tokens + delta)
            .execution_options(synchronize_session=False)
        )

    @classmethod
    async def count_conversations_by_user(cls, db: AsyncSession, user_id: int):
        """
        统计用户会话数量

        :param db: orm对象
        :param user_id: 用户ID
        :return: 会话数量
        """
        count = (
            await db.execute(
                select(func.count('*')).select_from(ChatConversation).where(ChatConversation.user_id == user_id)
            )
        ).scalar()
        return count

    # 标签相关方法

    @classmethod
    async def get_tag_by_id(cls, db: AsyncSession, tag_id: int):
        """
        根据标签id获取标签信息

        :param db: orm对象
        :param tag_id: 标签id
        :return: 标签信息对象
        """
        tag_info = (await db.execute(select(ChatConversationTag).where(ChatConversationTag.tag_id == tag_id))).scalars().first()
        return tag_info

    @classmethod
    async def get_tag_list_by_user(cls, db: AsyncSession, user_id: int):
        """
        获取用户所有标签

        :param db: orm对象
        :param user_id: 用户ID
        :return: 标签列表
        """
        tag_list = (
            await db.execute(
                select(ChatConversationTag)
                .where(ChatConversationTag.user_id == user_id)
                .order_by(ChatConversationTag.tag_id)
            )
        ).scalars().all()
        return tag_list

    @classmethod
    async def get_tag_by_name(cls, db: AsyncSession, user_id: int, tag_name: str):
        """
        根据标签名称获取标签信息

        :param db: orm对象
        :param user_id: 用户ID
        :param tag_name: 标签名称
        :return: 标签信息对象
        """
        tag_info = (
            await db.execute(
                select(ChatConversationTag).where(
                    ChatConversationTag.user_id == user_id,
                    ChatConversationTag.tag_name == tag_name,
                )
            )
        ).scalars().first()
        return tag_info

    @classmethod
    async def add_tag(cls, db: AsyncSession, tag):
        """
        新增标签

        :param db: orm对象
        :param tag: 标签对象
        :return: 标签对象
        """
        db.add(tag)
        await db.flush()
        return tag

    @classmethod
    async def delete_tag(cls, db: AsyncSession, tag_ids: list):
        """
        删除标签

        :param db: orm对象
        :param tag_ids: 标签ID列表
        :return:
        """
        await db.execute(delete(ChatConversationTag).where(ChatConversationTag.tag_id.in_(tag_ids)))
