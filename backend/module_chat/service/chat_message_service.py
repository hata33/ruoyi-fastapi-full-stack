"""
聊天消息管理 Service（服务层）

说明：
- 封装消息管理相关的业务逻辑
- 负责消息发送、流式输出、停止生成等
- 使用UUID作为消息和会话ID
"""

import json
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from exceptions.exception import ServiceException

from module_chat.config.constants import (
    AttachmentConfig,
    ChatErrorCode,
    ConversationConfig,
    MessageContext,
    MessageRole,
    ModelConfig,
    SSEEventType,
    UserIds,
)
from module_chat.dao.chat_conversation_dao import ChatConversationDao
from module_chat.dao.chat_message_dao import ChatMessageDao
from module_chat.dao.chat_model_dao import ChatModelDao
from module_chat.entity.do.chat_message_do import ChatMessage
from module_chat.entity.vo.chat_message_vo import (
    ChatMessageModel,
    MessageListModel,
    RegenerateMessageModel,
    SendMessageModel,
)
from module_chat.entity.vo.common_vo import CrudResponseModel
from module_chat.utils.uuid_util import generate_uuid, is_valid_uuid
from utils.common_util import CamelCaseUtil
from utils.log_util import logger


class ChatMessageService:
    """
    聊天消息管理模块服务层
    """

    @classmethod
    async def get_message_list_services(
        cls,
        query_db: AsyncSession,
        conversation_id: str,
        user_id: int,
        before_message_id: Optional[str] = None,
        page_size: int = MessageContext.MAX_RECENT_MESSAGES,
    ):
        """
        获取消息列表service

        :param query_db: orm对象
        :param conversation_id: 会话ID（UUID）
        :param user_id: 用户ID
        :param before_message_id: 获取此消息之前的消息（UUID）
        :param page_size: 每页数量
        :return: 消息列表
        """
        # 验证UUID格式
        if not is_valid_uuid(conversation_id):
            raise ServiceException(message='会话ID格式错误')

        # 验证会话权限
        conversation = await ChatConversationDao.get_conversation_by_id(query_db, conversation_id)
        if not conversation:
            raise ServiceException(message='会话不存在', code=ChatErrorCode.CONVERSATION_NOT_FOUND)

        if conversation.user_id != user_id:
            raise ServiceException(message='没有权限访问此会话', code=ChatErrorCode.PERMISSION_DENIED)

        # 获取消息列表
        messages = await ChatMessageDao.get_message_list_by_conversation(
            query_db, conversation_id, before_message_id, page_size
        )

        # 转换为VO并处理附件字段
        message_list = []
        for msg in messages:
            msg_dict = CamelCaseUtil.transform_result(msg)
            # 处理attachments字段：从JSON字符串转换为列表
            if msg_dict.get('attachments'):
                try:
                    msg_dict['attachments'] = (
                        json.loads(msg_dict['attachments'])
                        if isinstance(msg_dict['attachments'], str)
                        else msg_dict['attachments']
                    )
                except json.JSONDecodeError as e:
                    logger.warning(f'附件数据JSON解析失败: {e}, message_id: {msg_dict.get("message_id")}')
                    msg_dict['attachments'] = []
            else:
                msg_dict['attachments'] = []
            # 创建VO对象
            msg_vo = ChatMessageModel(**msg_dict)
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
        :return: 消息ID（UUID）
        """
        # 验证UUID格式
        if not is_valid_uuid(page_object.conversation_id):
            raise ServiceException(message='会话ID格式错误')

        # 验证会话权限
        conversation = await ChatConversationDao.get_conversation_by_id(query_db, page_object.conversation_id)
        if not conversation:
            raise ServiceException(message='会话不存在', code=ChatErrorCode.CONVERSATION_NOT_FOUND)

        if conversation.user_id != user_id:
            raise ServiceException(message='没有权限访问此会话', code=ChatErrorCode.PERMISSION_DENIED)

        # 确定使用的模型
        model_id = page_object.model_id or conversation.model_id

        # 验证模型是否存在且启用
        model_info = await ChatModelDao.get_model_by_code(query_db, model_id)
        if model_info:
            if not model_info.is_enabled:
                raise ServiceException(message='模型已禁用', code=ChatErrorCode.MODEL_DISABLED)
        else:
            # 检查是否在允许的模型列表中
            if model_id not in ModelConfig.ALLOWED_MODELS:
                raise ServiceException(
                    message=f'模型 [{model_id}] 不存在或不在允许列表中',
                    code=ChatErrorCode.MODEL_NOT_FOUND,
                )
            logger.warning(f'模型 [{model_id}] 在数据库中不存在，但允许使用')

        # 验证附件数量
        if page_object.attachments and len(page_object.attachments) > AttachmentConfig.MAX_ATTACHMENTS_PER_MESSAGE:
            raise ServiceException(
                message=f'附件数量超过限制，最多{AttachmentConfig.MAX_ATTACHMENTS_PER_MESSAGE}个',
                code=ChatErrorCode.INVALID_ATTACHMENT,
            )

        # 生成消息ID（UUID）
        message_id = generate_uuid()

        # 创建用户消息（使用数据库实体）
        user_message = ChatMessage(
            message_id=message_id,
            conversation_id=page_object.conversation_id,
            role=MessageRole.USER,
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
                title = cls._generate_conversation_title(page_object.content)
                await ChatConversationDao.edit_conversation(
                    query_db,
                    {
                        'conversation_id': page_object.conversation_id,
                        'title': title,
                        'update_time': datetime.now(),
                    },
                )

            await query_db.commit()

            # 返回用户消息ID，后续用于流式生成
            return user_msg.message_id

        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    def _generate_conversation_title(cls, content: str) -> str:
        """
        生成会话标题

        :param content: 消息内容
        :return: 标题字符串
        """
        # 去除首尾空白
        content = content.strip()

        # 检查是否为空
        if not content:
            return ConversationConfig.DEFAULT_TITLE

        # 限制标题长度
        if len(content) > ConversationConfig.TITLE_PREVIEW_LENGTH:
            title = content[: ConversationConfig.TITLE_PREVIEW_LENGTH] + '...'
        else:
            title = content

        return title

    @classmethod
    async def stop_generation_services(cls, query_db: AsyncSession, message_id: str, user_id: int):
        """
        停止生成service

        :param query_db: orm对象
        :param message_id: 消息ID（UUID）
        :param user_id: 用户ID
        :return: 操作结果
        """
        # 验证UUID格式
        if not is_valid_uuid(message_id):
            raise ServiceException(message='消息ID格式错误')

        # 尝试查找消息
        message = await ChatMessageDao.get_message_by_id(query_db, message_id)

        # 如果消息不存在，可能是正在流式生成中还未保存到数据库
        # 这种情况下直接返回成功，让前端清除流式状态即可
        if not message:
            logger.info(f'消息 {message_id} 在数据库中不存在，可能正在生成中，返回停止成功')
            return CrudResponseModel(is_success=True, message='已停止生成', data={'content': '', 'tokens_used': 0})

        # 验证权限
        conversation = await ChatConversationDao.get_conversation_by_id(query_db, message.conversation_id)
        if conversation.user_id != user_id:
            raise ServiceException(message='没有权限操作此消息', code=ChatErrorCode.PERMISSION_DENIED)

        # TODO: 实现真正的停止逻辑
        # 需要建立生成任务管理机制，设置停止标志并通知生成器
        return CrudResponseModel(is_success=True, message='已停止生成', data={'content': message.content, 'tokens_used': message.tokens_used or 0})

    @classmethod
    async def regenerate_message_services(
        cls, query_db: AsyncSession, message_id: str, page_object: RegenerateMessageModel, user_id: int
    ):
        """
        重新生成消息service

        :param query_db: orm对象
        :param message_id: 要重新生成的用户消息ID（UUID）
        :param page_object: 重新生成参数
        :param user_id: 用户ID
        :return: (用户消息ID, 会话ID, 模型ID, 消息历史)
        """
        # 验证UUID格式
        if not is_valid_uuid(message_id):
            raise ServiceException(message='消息ID格式错误')

        # 验证消息存在且是用户消息
        message = await ChatMessageDao.get_message_by_id(query_db, message_id)
        if not message:
            raise ServiceException(message='消息不存在', code=ChatErrorCode.MESSAGE_NOT_FOUND)

        if message.role != MessageRole.USER:
            raise ServiceException(message='只能重新生成用户消息的回复')

        # 验证权限
        conversation = await ChatConversationDao.get_conversation_by_id(query_db, message.conversation_id)
        if not conversation or conversation.user_id != user_id:
            raise ServiceException(message='没有权限操作此消息', code=ChatErrorCode.PERMISSION_DENIED)

        # 如果指定了新模型，更新会话模型
        model_id = page_object.model_id or conversation.model_id
        if page_object.model_id:
            # 验证新模型是否允许使用
            if page_object.model_id not in ModelConfig.ALLOWED_MODELS:
                raise ServiceException(
                    message=f'模型 [{page_object.model_id}] 不在允许列表中',
                    code=ChatErrorCode.MODEL_NOT_FOUND,
                )
            await ChatConversationDao.edit_conversation(
                query_db,
                {
                    'conversation_id': message.conversation_id,
                    'model_id': page_object.model_id,
                    'update_time': datetime.now(),
                },
            )

        # 构建消息历史（不包括当前用户消息之后的AI回复）
        messages = await ChatMessageDao.get_messages_before(query_db, message.conversation_id, message_id)

        # 转换为API格式
        message_list = []
        for msg in messages:
            message_list.append({'role': msg.role, 'content': msg.content})

        # 添加用户消息
        message_list.append({'role': MessageRole.USER, 'content': message.content})

        return message_id, message.conversation_id, model_id, message_list

    @classmethod
    async def replace_assistant_message_services(
        cls, query_db: AsyncSession, conversation_id: str, content: str, thinking_content: str = None, tokens_used: int = 0
    ):
        """
        替换最后一条AI助手消息service（用于重新生成）

        :param query_db: orm对象
        :param conversation_id: 会话ID（UUID）
        :param content: 消息内容
        :param thinking_content: 推理过程内容
        :param tokens_used: 使用的token数
        :return: 消息ID（UUID）
        """
        # 获取最后一条消息
        last_message = await ChatMessageDao.get_last_message(query_db, conversation_id)

        if last_message and last_message.role == MessageRole.ASSISTANT:
            # 更新最后一条助手消息
            await ChatMessageDao.update_message_content(query_db, last_message.message_id, content, thinking_content, tokens_used)
            message_id = last_message.message_id
        else:
            # 生成新消息ID（UUID）
            message_id = generate_uuid()

            # 创建新的助手消息
            assistant_message = ChatMessage(
                message_id=message_id,
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=content,
                thinking_content=thinking_content,
                tokens_used=tokens_used,
                user_id=UserIds.AI,  # AI消息使用常量
                create_time=datetime.now(),
                update_time=datetime.now(),
            )
            msg = await ChatMessageDao.add_message(query_db, assistant_message)
            message_id = msg.message_id

        # 更新会话累计token数
        if tokens_used > 0:
            await ChatConversationDao.update_conversation_tokens(query_db, conversation_id, tokens_used)

        await query_db.commit()
        return message_id

    @classmethod
    async def create_assistant_message_services(
        cls, query_db: AsyncSession, conversation_id: str, content: str, thinking_content: str = None, tokens_used: int = 0
    ):
        """
        创建AI助手消息service

        :param query_db: orm对象
        :param conversation_id: 会话ID（UUID）
        :param content: 消息内容
        :param thinking_content: 推理过程内容
        :param tokens_used: 使用的token数
        :return: 消息ID（UUID）
        """
        # 生成消息ID（UUID）
        message_id = generate_uuid()

        assistant_message = ChatMessage(
            message_id=message_id,
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=content,
            thinking_content=thinking_content,
            tokens_used=tokens_used,
            user_id=UserIds.AI,  # AI消息使用常量
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
    async def build_conversation_messages(cls, query_db: AsyncSession, conversation_id: str, new_content: str, user_id: int) -> list:
        """
        构建对话消息历史（用于 AI API 调用）

        :param query_db: orm对象
        :param conversation_id: 会话ID（UUID）
        :param new_content: 新消息内容
        :param user_id: 用户ID
        :return: 消息历史列表
        """
        # 验证UUID格式
        if not is_valid_uuid(conversation_id):
            raise ServiceException(message='会话ID格式错误')

        # 验证会话权限
        conversation = await ChatConversationDao.get_conversation_by_id(query_db, conversation_id)
        if not conversation or conversation.user_id != user_id:
            raise ServiceException(message='会话不存在或没有权限')

        # 获取历史消息（使用配置的限制数量）
        messages = await ChatMessageDao.get_recent_messages(
            query_db, conversation_id, limit=MessageContext.MAX_RECENT_MESSAGES
        )

        # 构建消息列表
        message_list = []
        for msg in messages:
            message_list.append({'role': msg.role, 'content': msg.content})

        # 添加新消息
        message_list.append({'role': MessageRole.USER, 'content': new_content})

        return message_list
