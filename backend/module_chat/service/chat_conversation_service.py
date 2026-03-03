"""
聊天会话管理 Service（服务层）

说明：
- 封装会话管理相关的业务逻辑
- 负责会话的CRUD、标签管理、置顶等
"""

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from exceptions.exception import ServiceException
from module_chat.dao.chat_conversation_dao import ChatConversationDao
from module_chat.dao.chat_message_dao import ChatMessageDao
from module_chat.entity.do.chat_conversation_do import ChatConversation
from module_chat.entity.vo.chat_conversation_vo import (
    AddChatConversationModel,
    ChatConversationModel,
    DeleteChatConversationModel,
    PinConversationModel,
)
from module_chat.entity.vo.common_vo import CrudResponseModel
from utils.common_util import CamelCaseUtil
from utils.log_util import logger
import json


class ChatConversationService:
    """
    聊天会话管理模块服务层
    """

    @classmethod
    async def get_conversation_list_services(
        cls, query_db: AsyncSession, query_object, is_page: bool = True
    ):
        """
        获取会话列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否分页
        :return: 会话列表信息对象
        """
        conversation_list_result = await ChatConversationDao.get_conversation_list(query_db, query_object, is_page)

        # 处理tagList字段（已被CamelCaseUtil转换为驼峰命名）
        if is_page and hasattr(conversation_list_result, 'rows'):
            for row in conversation_list_result.rows:
                tag_list = row.get('tagList') if isinstance(row, dict) else getattr(row, 'tagList', None)
                if tag_list:
                    try:
                        tag_list_parsed = json.loads(tag_list) if isinstance(tag_list, str) else tag_list
                        if isinstance(row, dict):
                            row['tagList'] = tag_list_parsed
                        else:
                            row.tagList = tag_list_parsed
                    except:
                        if isinstance(row, dict):
                            row['tagList'] = []
                        else:
                            row.tagList = []
                else:
                    if isinstance(row, dict):
                        row['tagList'] = []
                    else:
                        row.tagList = []
        elif not is_page:
            for row in conversation_list_result:
                tag_list = row.get('tagList') if isinstance(row, dict) else getattr(row, 'tagList', None)
                if tag_list:
                    try:
                        tag_list_parsed = json.loads(tag_list) if isinstance(tag_list, str) else tag_list
                        if isinstance(row, dict):
                            row['tagList'] = tag_list_parsed
                        else:
                            row.tagList = tag_list_parsed
                    except:
                        if isinstance(row, dict):
                            row['tagList'] = []
                        else:
                            row.tagList = []
                else:
                    if isinstance(row, dict):
                        row['tagList'] = []
                    else:
                        row.tagList = []

        return conversation_list_result

    @classmethod
    async def get_conversation_detail_services(cls, query_db: AsyncSession, conversation_id: int, include_messages: bool = False):
        """
        获取会话详细信息service

        :param query_db: orm对象
        :param conversation_id: 会话id
        :param include_messages: 是否包含消息列表
        :return: 会话详细信息对象
        """
        conversation = await ChatConversationDao.get_conversation_by_id(query_db, conversation_id)
        if not conversation:
            raise ServiceException(message='会话不存在')

        result = ChatConversationModel(**CamelCaseUtil.transform_result(conversation))

        # 处理tag_list字段
        if result.tag_list:
            try:
                result.tag_list = json.loads(result.tag_list) if isinstance(result.tag_list, str) else result.tag_list
            except:
                result.tag_list = []
        else:
            result.tag_list = []

        # 如果需要包含消息列表
        if include_messages:
            from module_chat.entity.vo.chat_message_vo import ChatMessageModel

            messages = await ChatMessageDao.get_conversation_messages(query_db, conversation_id)
            message_list = [ChatMessageModel(**CamelCaseUtil.transform_result(m)) for m in messages]
            result.message_list = message_list
        else:
            result.message_list = []

        return result

    @classmethod
    async def add_conversation_services(cls, query_db: AsyncSession, page_object: AddChatConversationModel, user_id: int):
        """
        新增会话信息service

        :param query_db: orm对象
        :param page_object: 新增会话对象
        :param user_id: 用户ID
        :return: 新增会话校验结果
        """
        # 构建会话对象
        conversation = ChatConversation(
            title=page_object.title or '新对话',
            model_id=page_object.model_id or 'deepseek-chat',
            user_id=user_id,
            tag_list=json.dumps(page_object.tag_list or [], ensure_ascii=False),
            is_pinned=False,
            total_tokens=0,
            message_count=0,
            create_time=datetime.now(),
            update_time=datetime.now(),
        )

        try:
            add_conversation = await ChatConversationDao.add_conversation(query_db, conversation)
            await query_db.commit()

            # 使用 CamelCaseUtil 转换为驼峰命名
            result = CamelCaseUtil.transform_result(add_conversation)
            return CrudResponseModel(is_success=True, message='创建成功', result=result)
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_conversation_services(cls, query_db: AsyncSession, page_object, user_id: int):
        """
        编辑会话信息service

        :param query_db: orm对象
        :param page_object: 编辑会话对象
        :param user_id: 用户ID
        :return: 编辑会话校验结果
        """
        # 检查会话是否存在且属于当前用户
        conversation = await ChatConversationDao.get_conversation_by_id(query_db, page_object.conversation_id)
        if not conversation:
            raise ServiceException(message='会话不存在')

        if conversation.user_id != user_id:
            raise ServiceException(message='没有权限操作此会话')

        # 构建更新数据
        update_data = {
            'conversation_id': page_object.conversation_id,
            'update_time': datetime.now(),
        }

        if page_object.title is not None:
            update_data['title'] = page_object.title

        if page_object.model_id is not None:
            update_data['model_id'] = page_object.model_id

        if page_object.tag_list is not None:
            update_data['tag_list'] = json.dumps(page_object.tag_list, ensure_ascii=False)

        try:
            await ChatConversationDao.edit_conversation(query_db, update_data)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def delete_conversation_services(cls, query_db: AsyncSession, page_object: DeleteChatConversationModel, user_id: int):
        """
        删除会话信息service

        :param query_db: orm对象
        :param page_object: 删除会话对象
        :param user_id: 用户ID
        :return: 删除会话校验结果
        """
        if page_object.conversation_ids:
            conversation_id_list = [int(cid) for cid in page_object.conversation_ids.split(',')]

            # 验证所有会话都属于当前用户
            for conversation_id in conversation_id_list:
                conversation = await ChatConversationDao.get_conversation_by_id(query_db, conversation_id)
                if not conversation:
                    raise ServiceException(message=f'会话{conversation_id}不存在')
                if conversation.user_id != user_id:
                    raise ServiceException(message='没有权限操作此会话')

            try:
                # 先删除关联的消息
                for conversation_id in conversation_id_list:
                    await ChatMessageDao.delete_conversation_messages(query_db, conversation_id)

                # 再删除会话
                await ChatConversationDao.delete_conversation(query_db, conversation_id_list)

                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入会话id为空')

    @classmethod
    async def pin_conversation_services(cls, query_db: AsyncSession, conversation_id: int, page_object: PinConversationModel, user_id: int):
        """
        置顶/取消置顶会话service

        :param query_db: orm对象
        :param conversation_id: 会话ID
        :param page_object: 置顶对象
        :param user_id: 用户ID
        :return: 操作结果
        """
        conversation = await ChatConversationDao.get_conversation_by_id(query_db, conversation_id)
        if not conversation:
            raise ServiceException(message='会话不存在')

        if conversation.user_id != user_id:
            raise ServiceException(message='没有权限操作此会话')

        try:
            pin_time = datetime.now() if page_object.is_pinned else None
            await ChatConversationDao.update_conversation_pin(query_db, conversation_id, page_object.is_pinned, pin_time)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='操作成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def get_conversation_context_services(cls, query_db: AsyncSession, conversation_id: int, user_id: int):
        """
        获取会话上下文状态service

        :param query_db: orm对象
        :param conversation_id: 会话ID
        :param user_id: 用户ID
        :return: 上下文状态对象
        """
        from module_chat.entity.vo.chat_conversation_vo import ConversationContextModel

        conversation = await ChatConversationDao.get_conversation_by_id(query_db, conversation_id)
        if not conversation:
            raise ServiceException(message='会话不存在')

        if conversation.user_id != user_id:
            raise ServiceException(message='没有权限访问此会话')

        # 获取模型最大token数
        from module_chat.dao.chat_model_dao import ChatModelDao
        model_info = await ChatModelDao.get_model_by_code(query_db, conversation.model_id)
        max_tokens = model_info.max_tokens if model_info else 64000

        # 计算使用百分比
        total_tokens = conversation.total_tokens or 0
        usage_percent = int((total_tokens / max_tokens) * 100) if max_tokens > 0 else 0

        # 确定警告级别
        if usage_percent >= 90:
            warning_level = 'critical'
        elif usage_percent >= 80:
            warning_level = 'warning'
        else:
            warning_level = 'normal'

        result = ConversationContextModel(
            total_tokens=total_tokens,
            max_tokens=max_tokens,
            usage_percent=usage_percent,
            message_count=conversation.message_count or 0,
            warning_level=warning_level,
        )

        return result

    @classmethod
    async def export_conversation_services(cls, query_db: AsyncSession, conversation_id: int, format_type: str, user_id: int):
        """
        导出会话service

        :param query_db: orm对象
        :param conversation_id: 会话ID
        :param format_type: 导出格式
        :param user_id: 用户ID
        :return: 导出结果
        """
        from module_chat.entity.vo.chat_conversation_vo import ExportConversationModel

        conversation = await ChatConversationDao.get_conversation_by_id(query_db, conversation_id)
        if not conversation:
            raise ServiceException(message='会话不存在')

        if conversation.user_id != user_id:
            raise ServiceException(message='没有权限导出此会话')

        # 这里简化处理，实际应该生成文件并返回下载链接
        file_name = f"{conversation.title}_{datetime.now().strftime('%Y%m%d')}.{format_type}"
        download_url = f"/api/chat/files/download/{conversation_id}.{format_type}"

        result = ExportConversationModel(
            download_url=download_url,
            file_name=file_name,
            file_size=0,
        )

        return result

    # 标签相关方法

    @classmethod
    async def get_tag_list_services(cls, query_db: AsyncSession, user_id: int):
        """
        获取用户标签列表service

        :param query_db: orm对象
        :param user_id: 用户ID
        :return: 标签列表
        """
        from module_chat.entity.vo.chat_conversation_vo import ChatConversationTagModel

        tag_list = await ChatConversationDao.get_tag_list_by_user(query_db, user_id)
        result = []

        for tag in tag_list:
            # 统计该标签关联的会话数（简化处理，实际需要解析tag_list字段）
            tag_model = ChatConversationTagModel(**CamelCaseUtil.transform_result(tag))
            tag_model.conversation_count = 0  # 暂时设为0，实际需要统计
            result.append(tag_model)

        return result

    @classmethod
    async def add_tag_services(cls, query_db: AsyncSession, page_object, user_id: int):
        """
        新增标签service

        :param query_db: orm对象
        :param page_object: 新增标签对象
        :param user_id: 用户ID
        :return: 新增标签校验结果
        """
        # 检查标签名称是否已存在
        existing_tag = await ChatConversationDao.get_tag_by_name(query_db, user_id, page_object.tag_name)
        if existing_tag:
            raise ServiceException(message='标签名称已存在')

        try:
            from module_chat.entity.do.chat_conversation_tag_do import ChatConversationTag

            tag = ChatConversationTag(
                tag_name=page_object.tag_name,
                tag_color=page_object.tag_color,
                user_id=user_id,
                create_time=datetime.now(),
                update_time=datetime.now(),
            )

            new_tag = await ChatConversationDao.add_tag(query_db, tag)
            await query_db.commit()

            result = {
                'tag_id': new_tag.tag_id,
                'tag_name': new_tag.tag_name,
                'tag_color': new_tag.tag_color,
            }
            return CrudResponseModel(is_success=True, message='创建成功', result=result)
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def delete_tag_services(cls, query_db: AsyncSession, page_object, user_id: int):
        """
        删除标签service

        :param query_db: orm对象
        :param page_object: 删除标签对象
        :param user_id: 用户ID
        :return: 删除标签校验结果
        """
        if page_object.tag_ids:
            tag_id_list = [int(tid) for tid in page_object.tag_ids.split(',')]

            # 验证所有标签都属于当前用户
            for tag_id in tag_id_list:
                tag = await ChatConversationDao.get_tag_by_id(query_db, tag_id)
                if not tag:
                    raise ServiceException(message=f'标签{tag_id}不存在')
                if tag.user_id != user_id:
                    raise ServiceException(message='没有权限操作此标签')

            try:
                await ChatConversationDao.delete_tag(query_db, tag_id_list)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入标签id为空')
