"""
聊天消息管理 Controller（控制器）

说明：
- 定义消息管理相关的HTTP接口
- 包括发送消息、流式输出、停止生成、重新生成、消息列表等
"""

import json
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.login_service import LoginService
from module_chat.entity.vo.chat_message_vo import MessageListModel, RegenerateMessageModel, SendMessageModel
from module_chat.service.chat_message_service import ChatMessageService
from module_chat.service.deepseek_client import get_deepseek_client
from utils.log_util import logger
from utils.response_util import ResponseUtil


chatMessageController = APIRouter(prefix='/api/chat/messages', dependencies=[Depends(LoginService.get_current_user)])


@chatMessageController.post(
    '/stream',
    dependencies=[Depends(CheckUserInterfaceAuth('chat:message:send'))],
)
async def send_message_stream(
    request: Request,
    send_message: SendMessageModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    发送消息（流式）

    :param send_message: 发送消息对象
    :return: SSE流
    """
    # 创建用户消息
    user_message_id = await ChatMessageService.send_message_services(
        query_db, send_message, current_user.user.user_id
    )

    async def generate_stream():
        """生成流式响应"""
        try:
            # 获取 DeepSeek 客户端
            deepseek_client = get_deepseek_client()

            # 构建消息历史
            messages = await ChatMessageService.build_conversation_messages(
                query_db,
                send_message.conversation_id,
                send_message.content,
                current_user.user.user_id
            )

            # 发送message_start事件
            yield f"event: message_start\ndata: {json.dumps({'messageId': user_message_id})}\n\n"

            # 准备响应内容
            response_content = ""
            thinking_content = ""

            # 调用 DeepSeek API
            async for event in deepseek_client.chat_stream(
                messages=messages,
                model=send_message.model_id or deepseek_client.MODEL_CHAT,
                temperature=send_message.temperature,
                top_p=send_message.top_p,
                max_tokens=send_message.max_tokens,
            ):
                event_type = event.get("event")
                event_data = event.get("data", {})

                if event_type == "thinking_start":
                    yield f"event: thinking_start\ndata: {json.dumps({})}\n\n"

                elif event_type == "thinking_delta":
                    thinking_content += event_data.get("content", "")
                    yield f"event: thinking_delta\ndata: {json.dumps({'content': event_data.get('content', '')})}\n\n"

                elif event_type == "thinking_end":
                    yield f"event: thinking_end\ndata: {json.dumps({})}\n\n"

                elif event_type == "content_delta":
                    response_content += event_data.get("content", "")
                    yield f"event: content_delta\ndata: {json.dumps({'content': event_data.get('content', '')})}\n\n"

                elif event_type == "message_end":
                    # 创建助手消息记录
                    await ChatMessageService.create_assistant_message_services(
                        query_db,
                        send_message.conversation_id,
                        response_content,
                        thinking_content if thinking_content else None,
                        event_data.get("tokens_used", 0),
                    )

                    # 发送结束事件
                    yield f"event: message_end\ndata: {json.dumps({**event_data})}\n\n"
                    break

        except Exception as e:
            logger.error(f'流式生成失败: {str(e)}')
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate_stream(), media_type="text/event-stream")


@chatMessageController.post(
    '/{message_id}/stop',
    dependencies=[Depends(CheckUserInterfaceAuth('chat:message:stop'))],
)
@Log(title='消息管理', business_type=BusinessType.UPDATE)
async def stop_generation(
    request: Request,
    message_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    停止生成

    :param message_id: 消息ID
    :return: 操作结果
    """
    stop_result = await ChatMessageService.stop_generation_services(query_db, message_id, current_user.user.user_id)
    logger.info(stop_result.message)

    return ResponseUtil.success(msg=stop_result.message)


@chatMessageController.post(
    '/{message_id}/regenerate',
    dependencies=[Depends(CheckUserInterfaceAuth('chat:message:regenerate'))],
)
async def regenerate_message(
    request: Request,
    message_id: int,
    regenerate_message: RegenerateMessageModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    重新生成消息

    :param message_id: 消息ID（用户消息）
    :param regenerate_message: 重新生成参数
    :return: SSE流
    """
    # 获取用户消息ID和相关信息
    user_message_id, conversation_id, model_id, messages = await ChatMessageService.regenerate_message_services(
        query_db, message_id, regenerate_message, current_user.user.user_id
    )

    async def generate_regenerate_stream():
        """生成重新生成的流式响应"""
        try:
            # 获取 DeepSeek 客户端
            deepseek_client = get_deepseek_client()

            # 发送message_start事件
            yield f"event: message_start\ndata: {json.dumps({'messageId': user_message_id})}\n\n"

            # 准备响应内容
            response_content = ""
            thinking_content = ""

            # 调用 DeepSeek API
            async for event in deepseek_client.chat_stream(
                messages=messages,
                model=model_id or deepseek_client.MODEL_CHAT,
                temperature=regenerate_message.temperature,
                top_p=regenerate_message.top_p,
                max_tokens=regenerate_message.max_tokens,
            ):
                event_type = event.get("event")
                event_data = event.get("data", {})

                if event_type == "thinking_start":
                    yield f"event: thinking_start\ndata: {json.dumps({})}\n\n"

                elif event_type == "thinking_delta":
                    thinking_content += event_data.get("content", "")
                    yield f"event: thinking_delta\ndata: {json.dumps({'content': event_data.get('content', '')})}\n\n"

                elif event_type == "thinking_end":
                    yield f"event: thinking_end\ndata: {json.dumps({})}\n\n"

                elif event_type == "content_delta":
                    response_content += event_data.get("content", "")
                    yield f"event: content_delta\ndata: {json.dumps({'content': event_data.get('content', '')})}\n\n"

                elif event_type == "message_end":
                    # 创建助手消息记录（注意：这里需要替换之前的助手消息）
                    await ChatMessageService.replace_assistant_message_services(
                        query_db,
                        conversation_id,
                        response_content,
                        thinking_content if thinking_content else None,
                        event_data.get("tokens_used", 0),
                    )

                    # 发送结束事件
                    yield f"event: message_end\ndata: {json.dumps({**event_data})}\n\n"
                    break

        except Exception as e:
            logger.error(f'重新生成失败: {str(e)}')
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate_regenerate_stream(), media_type="text/event-stream")
