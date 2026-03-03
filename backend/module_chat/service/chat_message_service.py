"""
聊天消息管理 Service（服务层）

说明：
- 封装消息管理相关的业务逻辑
- 负责消息发送、流式输出、停止生成等
"""

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from exceptions.exception import ServiceException
from module_chat.dao.chat_conversation_dao import ChatConversationDao
from module_chat.dao.chat_message_dao import ChatMessageDao
from module_chat.dao.chat_model_dao import ChatModelDao
from module_chat.entity.vo.chat_message_vo import ChatMessageModel, MessageListModel, RegenerateMessageModel, SendMessageModel
from module_chat.entity.vo.common_vo import CrudResponseModel
from utils.common_util import CamelCaseUtil
import json


class ChatMessageService:
    """
    聊天消息管理模块服务层
    """

    @classmethod
    async def get_message_list_services(
        cls, query_db: AsyncSession, conversation_id: int, user_id: int, before_message_id: int = None, page_size: int = 50
    ):
        """
        获取消息列表service

        :param query_db: orm对象
        :param conversation_id: 会话ID
        :param user_id: 用户ID
        :param before_message_id: 获取此消息之前的消息
        :param page_size: 每页数量
        :return: 消息列表
        """
        # 验证会话权限
        conversation = await ChatConversationDao.get_conversation_by_id(query_db, conversation_id)
        if not conversation:
            raise ServiceException(message='会话不存在')

        if conversation.user_id != user_id:
            raise ServiceException(message='没有权限访问此会话')

        # 获取消息列表
        messages = await ChatMessageDao.get_message_list_by_conversation(query_db, conversation_id, before_message_id, page_size)

        # 转换为VO并处理附件字段
        message_list = []
        for msg in messages:
            msg_vo = ChatMessageModel(**CamelCaseUtil.transform_result(msg))
            if msg_vo.attachments:
                try:
                    msg_vo.attachments = json.loads(msg_vo.attachments) if isinstance(msg_vo.attachments, str) else msg_vo.attachments
                except:
                    msg_vo.attachments = []
            else:
                msg_vo.attachments = []
            message_list.append(msg_vo)

        # 统计总消息数
        total = await ChatMessageDao.count_messages_by_conversation(query_db, conversation_id)

        # 判断是否有更多数据
        has_more = False
        if before_message_id:
            has_more = len(message_list) >= page_size
        else:
            has_more = total > len(message_list)

        result = MessageListModel(rows=message_list, total=total, has_more=has_more)

        return result

    @classmethod
    async def send_message_services(cls, query_db: AsyncSession, page_object: SendMessageModel, user_id: int):
        """
        发送消息service（流式）

        :param query_db: orm对象
        :param page_object: 发送消息对象
        :param user_id: 用户ID
        :return: 消息ID和生成器
        """
        # 验证会话权限
        conversation = await ChatConversationDao.get_conversation_by_id(query_db, page_object.conversation_id)
        if not conversation:
            raise ServiceException(message='会话不存在')

        if conversation.user_id != user_id:
            raise ServiceException(message='没有权限访问此会话')

        # 确定使用的模型
        model_id = page_object.model_id or conversation.model_id

        # 验证模型是否存在且启用
        model_info = await ChatModelDao.get_model_by_code(query_db, model_id)
        if not model_info or not model_info.is_enabled:
            raise ServiceException(message='模型不可用')

        # 创建用户消息
        user_message = ChatMessageModel(
            conversation_id=page_object.conversation_id,
            role='user',
            content=page_object.content,
            attachments=json.dumps(page_object.attachments or [], ensure_ascii=False),
            user_id=user_id,
            create_time=datetime.now(),
            update_time=datetime.now(),
        )

        try:
            user_msg = await ChatMessageDao.add_message(query_db, user_message)

            # 更新会话消息数量和更新时间
            await ChatConversationDao.update_conversation_message_count(query_db, page_object.conversation_id)

            # 如果是首条消息，更新会话标题
            if conversation.message_count == 0:
                title = page_object.content[:20] + '...' if len(page_object.content) > 20 else page_object.content
                from module_chat.entity.vo.chat_conversation_vo import UpdateChatConversationModel
                update_obj = UpdateChatConversationModel(
                    conversation_id=page_object.conversation_id,
                    title=title,
                )
                await ChatConversationDao.edit_conversation(
                    query_db, {
                        'conversation_id': page_object.conversation_id,
                        'title': title,
                        'update_time': datetime.now(),
                    }
                )

            await query_db.commit()

            # 返回用户消息ID，后续用于流式生成
            return user_msg.message_id

        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def stop_generation_services(cls, query_db: AsyncSession, message_id: int, user_id: int):
        """
        停止生成service

        :param query_db: orm对象
        :param message_id: 消息ID
        :param user_id: 用户ID
        :return: 操作结果
        """
        message = await ChatMessageDao.get_message_by_id(query_db, message_id)
        if not message:
            raise ServiceException(message='消息不存在')

        # 验证权限
        conversation = await ChatConversationDao.get_conversation_by_id(query_db, message.conversation_id)
        if conversation.user_id != user_id:
            raise ServiceException(message='没有权限操作此消息')

        # 这里简化处理，实际应该设置停止标志并通知生成器
        return CrudResponseModel(is_success=True, message='已停止生成')

    @classmethod
    async def regenerate_message_services(cls, query_db: AsyncSession, message_id: int, page_object: RegenerateMessageModel, user_id: int):
        """
        重新生成消息service

        :param query_db: orm对象
        :param message_id: 要重新生成的用户消息ID
        :param page_object: 重新生成参数
        :param user_id: 用户ID
        :return: 用户消息ID
        """
        # 验证消息存在且是用户消息
        message = await ChatMessageDao.get_message_by_id(query_db, message_id)
        if not message:
            raise ServiceException(message='消息不存在')

        if message.role != 'user':
            raise ServiceException(message='只能重新生成用户消息的回复')

        # 验证权限
        conversation = await ChatConversationDao.get_conversation_by_id(query_db, message.conversation_id)
        if not conversation or conversation.user_id != user_id:
            raise ServiceException(message='没有权限操作此消息')

        # 如果指定了新模型，更新会话模型
        if page_object.model_id:
            await ChatConversationDao.edit_conversation(
                query_db, {
                    'conversation_id': message.conversation_id,
                    'model_id': page_object.model_id,
                    'update_time': datetime.now(),
                }
            )

        # 返回用户消息ID，用于流式生成
        return message_id

    @classmethod
    async def create_assistant_message_services(
        cls, query_db: AsyncSession, conversation_id: int, content: str, thinking_content: str = None, tokens_used: int = 0
    ):
        """
        创建AI助手消息service

        :param query_db: orm对象
        :param conversation_id: 会话ID
        :param content: 消息内容
        :param thinking_content: 推理过程内容
        :param tokens_used: 使用的token数
        :return: 消息对象
        """
        assistant_message = ChatMessageModel(
            conversation_id=conversation_id,
            role='assistant',
            content=content,
            thinking_content=thinking_content,
            tokens_used=tokens_used,
            user_id=0,  # AI消息没有用户ID
            create_time=datetime.now(),
            update_time=datetime.now(),
        )

        try:
            msg = await ChatMessageDao.add_message(query_db, assistant_message)

            # 更新会话累计token数
            if tokens_used > 0:
                await ChatConversationDao.update_conversation_tokens(query_db, conversation_id, tokens_used)

            await query_db.commit()
            return msg.message_id
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def build_conversation_messages(
        cls, query_db: AsyncSession, conversation_id: int, new_content: str, user_id: int
    ) -> list:
        """
        构建对话消息历史（用于 AI API 调用）

        :param query_db: orm对象
        :param conversation_id: 会话ID
        :param new_content: 新消息内容
        :param user_id: 用户ID
        :return: 消息历史列表
        """
        # 验证会话权限
        conversation = await ChatConversationDao.get_conversation_by_id(query_db, conversation_id)
        if not conversation or conversation.user_id != user_id:
            raise ServiceException(message='会话不存在或没有权限')

        # 获取历史消息（限制最近50条以控制上下文长度）
        messages = await ChatMessageDao.get_recent_messages(query_db, conversation_id, limit=50)

        # 构建消息列表
        message_list = []
        for msg in messages:
            message_list.append({
                "role": msg.role,
                "content": msg.content
            })

        # 添加新消息
        message_list.append({
            "role": "user",
            "content": new_content
        })

        return message_list
