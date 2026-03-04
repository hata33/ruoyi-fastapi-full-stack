"""
聊天消息管理 DAO（Data Access Object）

说明：
- 负责消息相关的数据库操作
- 只处理数据访问，不包含业务逻辑
- 使用UUID作为消息ID
"""

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_chat.entity.do.chat_message_do import ChatMessage
from module_chat.entity.vo.chat_message_vo import ChatMessageModel
from typing import List, Optional


class ChatMessageDao:
    """
    聊天消息管理模块数据库操作层
    """

    @classmethod
    async def get_message_by_id(cls, db: AsyncSession, message_id: str):
        """
        根据消息id获取消息详细信息

        :param db: orm对象
        :param message_id: 消息ID（UUID）
        :return: 消息信息对象
        """
        message_info = (
            await db.execute(select(ChatMessage).where(ChatMessage.message_id == message_id))
        ).scalars().first()
        return message_info

    @classmethod
    async def get_message_list_by_conversation(
        cls, db: AsyncSession, conversation_id: str, before_message_id: Optional[str] = None, page_size: int = 50
    ):
        """
        获取会话的消息列表

        :param db: orm对象
        :param conversation_id: 会话ID（UUID）
        :param before_message_id: 获取此消息之前的消息（UUID）
        :param page_size: 每页数量
        :return: 消息列表
        """
        query = select(ChatMessage).where(ChatMessage.conversation_id == conversation_id)

        if before_message_id:
            # 对于UUID，使用字符串比较
            query = query.where(ChatMessage.message_id < before_message_id)

        query = query.order_by(ChatMessage.create_time.desc()).limit(page_size)

        message_list = (await db.execute(query)).scalars().all()
        # 返回时按时间正序
        return list(reversed(message_list))

    @classmethod
    async def get_conversation_messages(cls, db: AsyncSession, conversation_id: str):
        """
        获取会话的所有消息

        :param db: orm对象
        :param conversation_id: 会话ID（UUID）
        :return: 消息列表
        """
        message_list = (
            await db.execute(
                select(ChatMessage)
                .where(ChatMessage.conversation_id == conversation_id)
                .order_by(ChatMessage.create_time)
            )
        ).scalars().all()
        return message_list

    @classmethod
    async def get_recent_messages(cls, db: AsyncSession, conversation_id: str, limit: int = 50):
        """
        获取会话的最近N条消息（用于构建 AI 上下文）

        :param db: orm对象
        :param conversation_id: 会话ID（UUID）
        :param limit: 消息数量限制
        :return: 消息列表
        """
        message_list = (
            await db.execute(
                select(ChatMessage)
                .where(ChatMessage.conversation_id == conversation_id)
                .order_by(ChatMessage.create_time.desc())
                .limit(limit)
            )
        ).scalars().all()
        # 返回时按时间正序
        return list(reversed(message_list))

    @classmethod
    async def add_message(cls, db: AsyncSession, message):
        """
        新增消息

        :param db: orm对象
        :param message: 消息对象（ChatMessage DO实体或ChatMessageModel VO）
        :return: 消息对象
        """
        # 如果是VO模型，转换为DO实体
        if hasattr(message, 'model_dump'):
            # ChatMessageModel (VO)
            db_message = ChatMessage(**message.model_dump(by_alias=False, exclude_unset=True))
        else:
            # ChatMessage (DO实体)
            db_message = message
        db.add(db_message)
        await db.flush()
        return db_message

    @classmethod
    async def edit_message(cls, db: AsyncSession, message: dict):
        """
        编辑消息

        :param db: orm对象
        :param message: 需要更新的消息字典
        :return:
        """
        await db.execute(update(ChatMessage), [message])

    @classmethod
    async def update_message_content(
        cls, db: AsyncSession, message_id: str, content: str, thinking_content: str = None, tokens_used: int = 0
    ):
        """
        更新消息内容

        :param db: orm对象
        :param message_id: 消息ID（UUID）
        :param content: 消息内容
        :param thinking_content: 推理过程内容
        :param tokens_used: 使用的token数
        :return:
        """
        update_data = {'content': content}
        if thinking_content is not None:
            update_data['thinking_content'] = thinking_content
        if tokens_used > 0:
            update_data['tokens_used'] = tokens_used
        await db.execute(update(ChatMessage).where(ChatMessage.message_id == message_id), [update_data])

    @classmethod
    async def update_message_tokens(cls, db: AsyncSession, message_id: str, tokens_used: int):
        """
        更新消息token数

        :param db: orm对象
        :param message_id: 消息ID（UUID）
        :param tokens_used: 使用的token数
        :return:
        """
        await db.execute(
            update(ChatMessage).where(ChatMessage.message_id == message_id).values(tokens_used=tokens_used)
        )

    @classmethod
    async def delete_conversation_messages(cls, db: AsyncSession, conversation_id: str):
        """
        删除会话的所有消息

        :param db: orm对象
        :param conversation_id: 会话ID（UUID）
        :return:
        """
        await db.execute(delete(ChatMessage).where(ChatMessage.conversation_id == conversation_id))

    @classmethod
    async def count_messages_by_conversation(cls, db: AsyncSession, conversation_id: str):
        """
        统计会话消息数量

        :param db: orm对象
        :param conversation_id: 会话ID（UUID）
        :return: 消息数量
        """
        count = (
            await db.execute(
                select(func.count('*')).select_from(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
            )
        ).scalar()
        return count

    @classmethod
    async def get_last_message_by_conversation(cls, db: AsyncSession, conversation_id: str):
        """
        获取会话的最后一条消息

        :param db: orm对象
        :param conversation_id: 会话ID（UUID）
        :return: 消息对象
        """
        message = (
            await db.execute(
                select(ChatMessage)
                .where(ChatMessage.conversation_id == conversation_id)
                .order_by(ChatMessage.create_time.desc())
                .limit(1)
            )
        ).scalars().first()
        return message

    @classmethod
    async def get_last_message(cls, db: AsyncSession, conversation_id: str):
        """
        获取会话的最后一条消息（别名方法）

        :param db: orm对象
        :param conversation_id: 会话ID（UUID）
        :return: 消息对象
        """
        return await cls.get_last_message_by_conversation(db, conversation_id)

    @classmethod
    async def get_messages_before(cls, db: AsyncSession, conversation_id: str, before_message_id: str):
        """
        获取指定消息之前的所有消息

        :param db: orm对象
        :param conversation_id: 会话ID（UUID）
        :param before_message_id: 消息ID（UUID）
        :return: 消息列表
        """
        messages = (
            await db.execute(
                select(ChatMessage)
                .where(
                    ChatMessage.conversation_id == conversation_id,
                    ChatMessage.message_id < before_message_id
                )
                .order_by(ChatMessage.create_time.asc())
            )
        ).scalars().all()
        return messages

    @classmethod
    async def get_conversation_context_tokens(cls, db: AsyncSession, conversation_id: str):
        """
        获取会话累计token数

        :param db: orm对象
        :param conversation_id: 会话ID（UUID）
        :return: 累计token数
        """
        total_tokens = (
            await db.execute(
                select(func.sum(ChatMessage.tokens_used)).select_from(ChatMessage).where(
                    ChatMessage.conversation_id == conversation_id
                )
            )
        ).scalar()
        return total_tokens or 0
