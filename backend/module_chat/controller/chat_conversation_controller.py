"""
聊天会话管理 Controller（控制器）

说明：
- 定义会话管理相关的HTTP接口
- 包括会话列表、详情、创建、更新、删除、置顶、导出、标签管理等
"""

from fastapi import APIRouter, Depends, Request
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.login_service import LoginService
from module_chat.entity.vo.chat_conversation_vo import (
    AddChatConversationModel,
    AddChatConversationTagModel,
    DeleteChatConversationModel,
    PinConversationModel,
    UpdateChatConversationModel,
)
from module_chat.service.chat_conversation_service import ChatConversationService
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


chatConversationController = APIRouter(prefix='/api/chat/conversations', dependencies=[Depends(LoginService.get_current_user)])


@chatConversationController.get(
    '',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('chat:conversation:list'))],
)
async def get_conversation_list(
    request: Request,
    title: Optional[str] = None,
    model_id: Optional[str] = None,
    is_pinned: Optional[bool] = None,
    tag_id: Optional[int] = None,
    begin_time: Optional[str] = None,
    end_time: Optional[str] = None,
    page_num: int = 1,
    page_size: int = 20,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    获取会话列表（分页）

    :param title: 会话标题
    :param model_id: 模型ID
    :param is_pinned: 是否置顶
    :param tag_id: 标签ID
    :param begin_time: 开始时间
    :param end_time: 结束时间
    :param page_num: 页码
    :param page_size: 每页数量
    :return: 会话列表
    """
    from module_chat.entity.vo.chat_conversation_vo import ChatConversationPageQueryModel
    query_object = ChatConversationPageQueryModel(
        title=title,
        model_id=model_id,
        is_pinned=is_pinned,
        tag_id=tag_id,
        begin_time=begin_time,
        end_time=end_time,
        page_num=page_num,
        page_size=page_size,
        user_id=current_user.user.user_id,
    )

    conversation_page_query_result = await ChatConversationService.get_conversation_list_services(query_db, query_object, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=conversation_page_query_result)


@chatConversationController.get(
    '/{conversation_id}',
    dependencies=[Depends(CheckUserInterfaceAuth('chat:conversation:query'))],
)
async def get_conversation_detail(
    request: Request,
    conversation_id: str,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    获取会话详情

    :param conversation_id: 会话ID
    :return: 会话详情
    """
    detail_result = await ChatConversationService.get_conversation_detail_services(
        query_db, conversation_id, include_messages=True
    )
    logger.info(f'获取conversation_id为{conversation_id}的信息成功')

    return ResponseUtil.success(data=detail_result)


@chatConversationController.post(
    '',
    dependencies=[Depends(CheckUserInterfaceAuth('chat:conversation:add'))],
)
@ValidateFields(validate_model='add_conversation')
@Log(title='会话管理', business_type=BusinessType.INSERT)
async def add_conversation(
    request: Request,
    add_conversation: AddChatConversationModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    新建会话

    :param add_conversation: 新增会话对象
    :return: 操作结果
    """
    add_conversation_result = await ChatConversationService.add_conversation_services(
        query_db, add_conversation, current_user.user.user_id
    )
    logger.info(add_conversation_result.message)

    return ResponseUtil.success(data=add_conversation_result.result, msg=add_conversation_result.message)


@chatConversationController.put(
    '',
    dependencies=[Depends(CheckUserInterfaceAuth('chat:conversation:edit'))],
)
@ValidateFields(validate_model='edit_conversation')
@Log(title='会话管理', business_type=BusinessType.UPDATE)
async def edit_conversation(
    request: Request,
    edit_conversation: UpdateChatConversationModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    更新会话信息

    :param edit_conversation: 更新会话对象
    :return: 操作结果
    """
    edit_conversation_result = await ChatConversationService.edit_conversation_services(
        query_db, edit_conversation, current_user.user.user_id
    )
    logger.info(edit_conversation_result.message)

    return ResponseUtil.success(msg=edit_conversation_result.message)


@chatConversationController.delete(
    '/{conversation_ids}',
    dependencies=[Depends(CheckUserInterfaceAuth('chat:conversation:remove'))],
)
@Log(title='会话管理', business_type=BusinessType.DELETE)
async def delete_conversation(
    request: Request,
    conversation_ids: str,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    删除会话

    :param conversation_ids: 会话ID（逗号分隔）
    :return: 操作结果
    """
    delete_conversation = DeleteChatConversationModel(conversation_ids=conversation_ids)
    delete_conversation_result = await ChatConversationService.delete_conversation_services(
        query_db, delete_conversation, current_user.user.user_id
    )
    logger.info(delete_conversation_result.message)

    return ResponseUtil.success(msg=delete_conversation_result.message)


@chatConversationController.put(
    '/{conversation_id}/pin',
    dependencies=[Depends(CheckUserInterfaceAuth('chat:conversation:edit'))],
)
@Log(title='会话管理', business_type=BusinessType.UPDATE)
async def pin_conversation(
    request: Request,
    conversation_id: str,
    pin_conversation: PinConversationModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    置顶/取消置顶会话

    :param conversation_id: 会话ID
    :param pin_conversation: 置顶对象
    :return: 操作结果
    """
    pin_conversation_result = await ChatConversationService.pin_conversation_services(
        query_db, conversation_id, pin_conversation, current_user.user.user_id
    )
    logger.info(pin_conversation_result.message)

    return ResponseUtil.success(msg=pin_conversation_result.message)


@chatConversationController.get(
    '/{conversation_id}/context',
    dependencies=[Depends(CheckUserInterfaceAuth('chat:conversation:context'))],
)
async def get_conversation_context(
    request: Request,
    conversation_id: str,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    获取会话上下文状态

    :param conversation_id: 会话ID
    :return: 上下文状态
    """
    context_result = await ChatConversationService.get_conversation_context_services(
        query_db, conversation_id, current_user.user.user_id
    )
    logger.info(f'获取conversation_id为{conversation_id}的上下文状态成功')

    return ResponseUtil.success(data=context_result)


@chatConversationController.get(
    '/{conversation_id}/export',
    dependencies=[Depends(CheckUserInterfaceAuth('chat:conversation:export'))],
)
async def export_conversation(
    request: Request,
    conversation_id: str,
    format: str,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    导出会话

    :param conversation_id: 会话ID
    :param format: 导出格式
    :return: 导出结果
    """
    export_result = await ChatConversationService.export_conversation_services(
        query_db, conversation_id, format, current_user.user.user_id
    )
    logger.info(f'导出conversation_id为{conversation_id}的会话成功')

    return ResponseUtil.success(data=export_result)


@chatConversationController.get(
    '/{conversation_id}/messages',
    dependencies=[Depends(CheckUserInterfaceAuth('chat:message:list'))],
)
async def get_conversation_messages(
    request: Request,
    conversation_id: str,
    before_message_id: Optional[str] = None,
    page_size: int = 50,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    获取会话消息列表

    :param conversation_id: 会话ID
    :param before_message_id: 获取此消息之前的消息（向上滚动）
    :param page_size: 每页数量，默认50
    :return: 消息列表
    """
    from module_chat.service.chat_message_service import ChatMessageService

    message_list_result = await ChatMessageService.get_message_list_services(
        query_db, conversation_id, current_user.user.user_id, before_message_id, page_size
    )
    logger.info(f'获取会话{conversation_id}的消息列表成功')

    return ResponseUtil.success(data=message_list_result)


# 标签相关接口


chatTagController = APIRouter(prefix='/api/chat/tags', dependencies=[Depends(LoginService.get_current_user)])


@chatTagController.get(
    '',
    dependencies=[Depends(CheckUserInterfaceAuth('chat:tag:list'))],
)
async def get_tag_list(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    获取会话标签列表

    :return: 标签列表
    """
    tag_list_result = await ChatConversationService.get_tag_list_services(query_db, current_user.user.user_id)
    logger.info('获取成功')

    return ResponseUtil.success(data=tag_list_result)


@chatTagController.post(
    '',
    dependencies=[Depends(CheckUserInterfaceAuth('chat:tag:add'))],
)
@ValidateFields(validate_model='add_tag')
@Log(title='标签管理', business_type=BusinessType.INSERT)
async def add_tag(
    request: Request,
    add_tag: AddChatConversationTagModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    创建会话标签

    :param add_tag: 新增标签对象
    :return: 操作结果
    """
    add_tag_result = await ChatConversationService.add_tag_services(query_db, add_tag, current_user.user.user_id)
    logger.info(add_tag_result.message)

    return ResponseUtil.success(data=add_tag_result.result, msg=add_tag_result.message)


@chatTagController.delete(
    '/{tag_ids}',
    dependencies=[Depends(CheckUserInterfaceAuth('chat:tag:remove'))],
)
@Log(title='标签管理', business_type=BusinessType.DELETE)
async def delete_tag(
    request: Request,
    tag_ids: str,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    删除会话标签

    :param tag_ids: 标签ID（逗号分隔）
    :return: 操作结果
    """
    from module_chat.entity.vo.chat_conversation_vo import DeleteChatConversationTagModel
    delete_tag = DeleteChatConversationTagModel(tag_ids=tag_ids)
    delete_tag_result = await ChatConversationService.delete_tag_services(query_db, delete_tag, current_user.user.user_id)
    logger.info(delete_tag_result.message)

    return ResponseUtil.success(msg=delete_tag_result.message)
