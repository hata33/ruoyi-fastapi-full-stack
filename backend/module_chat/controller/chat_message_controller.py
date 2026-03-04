"""
聊天消息管理 Controller（控制器）

说明：
- 定义消息管理相关的HTTP接口
- 包括发送消息、流式输出、停止生成、重新生成、消息列表等
- 使用UUID作为消息和会话ID
"""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession

from config.enums import BusinessType
from config.get_db import get_db
from config.database import AsyncSessionLocal
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.login_service import LoginService
from module_chat.entity.vo.chat_message_vo import MessageListModel, RegenerateMessageModel, SendMessageModel
from module_chat.service.chat_message_service import ChatMessageService
from module_chat.service.deepseek_client import get_deepseek_client
from module_chat.utils.uuid_util import generate_uuid
from utils.log_util import logger
from utils.response_util import ResponseUtil

chatMessageController = APIRouter(prefix='/api/chat/messages')  # 移除 token 校验，方便调试


@chatMessageController.post('/stream')  # 移除权限检查，方便调试
async def send_message_stream(
    request: Request,
    send_message: SendMessageModel,
    query_db: AsyncSession = Depends(get_db),
):  # 移除 current_user 依赖
    """
    发送消息（流式）

    :param send_message: 发送消息对象
    :return: SSE流
    """
    # 调试模式：使用固定用户ID
    DEBUG_USER_ID = 1

    # 创建用户消息
    user_message_id = await ChatMessageService.send_message_services(
        query_db, send_message, DEBUG_USER_ID
    )

    # 生成临时 AI 消息 ID（使用UUID）
    assistant_message_id = generate_uuid()

    # 构建消息历史
    messages = await ChatMessageService.build_conversation_messages(
        query_db,
        send_message.conversation_id,
        send_message.content,
        DEBUG_USER_ID  # 使用固定用户ID
    )

    # 获取 DeepSeek 客户端
    deepseek_client = get_deepseek_client()

    # 使用队列实现真正的流式响应
    event_queue = asyncio.Queue()
    response_content = ""
    thinking_content = ""
    processing_done = asyncio.Event()

    async def process_stream():
        """后台任务：处理 DeepSeek API 流式响应"""
        nonlocal response_content, thinking_content
        try:
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
                    await event_queue.put(("thinking_start", {}))

                elif event_type == "thinking_delta":
                    thinking_content += event_data.get("content", "")
                    await event_queue.put(("thinking_delta", {"content": event_data.get("content", "")}))

                elif event_type == "thinking_end":
                    await event_queue.put(("thinking_end", {}))

                elif event_type == "content_delta":
                    response_content += event_data.get("content", "")
                    await event_queue.put(("content_delta", {"content": event_data.get("content", "")}))

                elif event_type == "message_end":
                    # 创建助手消息记录（使用新的数据库会话）
                    async with AsyncSessionLocal() as new_db:
                        final_message_id = await ChatMessageService.create_assistant_message_services(
                            new_db,
                            send_message.conversation_id,
                            response_content,
                            thinking_content if thinking_content else None,
                            event_data.get("tokens_used", 0),
                        )
                        await event_queue.put(("message_end", {
                            "messageId": final_message_id,
                            "content": response_content,
                            "thinkingContent": thinking_content if thinking_content else None,
                            "tokensUsed": event_data.get("tokens_used", 0),
                            "totalTokens": event_data.get("total_tokens", 0)
                        }))
                    break
        except Exception as e:
            await event_queue.put(("error", {"code": 1009, "message": str(e)}))
        finally:
            processing_done.set()

    # 启动后台任务
    asyncio.create_task(process_stream())

    async def event_generator():
        """从队列读取事件并流式输出"""
        # 发送 message_start 事件
        yield f"event: message_start\ndata: {json.dumps({'userMessageId': user_message_id, 'assistantMessageId': assistant_message_id, 'conversationId': send_message.conversation_id})}\n\n"

        while True:
            try:
                # 使用超时等待，避免永久阻塞
                event_type, event_data = await asyncio.wait_for(event_queue.get(), timeout=60.0)

                if event_type == "thinking_start":
                    yield f"event: thinking_start\ndata: {json.dumps(event_data)}\n\n"

                elif event_type == "thinking_delta":
                    yield f"event: thinking_delta\ndata: {json.dumps(event_data)}\n\n"

                elif event_type == "thinking_end":
                    yield f"event: thinking_end\ndata: {json.dumps(event_data)}\n\n"

                elif event_type == "content_delta":
                    yield f"event: content_delta\ndata: {json.dumps(event_data)}\n\n"

                elif event_type == "message_end":
                    yield f"event: message_end\ndata: {json.dumps(event_data)}\n\n"
                    break

                elif event_type == "error":
                    yield f"event: error\ndata: {json.dumps(event_data)}\n\n"
                    break

            except asyncio.TimeoutError:
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


@chatMessageController.post('/{message_id}/stop')  # 移除权限检查
@Log(title='消息管理', business_type=BusinessType.UPDATE)
async def stop_generation(
    request: Request,
    message_id: str,
    query_db: AsyncSession = Depends(get_db),
):  # 移除 current_user 依赖
    """
    停止生成

    :param message_id: AI消息ID（UUID）
    :return: 操作结果（包含已保存的消息信息）
    """
    from datetime import datetime
    DEBUG_USER_ID = 1

    stop_result = await ChatMessageService.stop_generation_services(query_db, message_id, DEBUG_USER_ID)
    logger.info(stop_result.message)

    return ResponseUtil.success(
        data={
            'messageId': message_id,
            'content': stop_result.data.get('content', '') if hasattr(stop_result, 'data') and stop_result.data else '',
            'tokensUsed': stop_result.data.get('tokens_used', 0) if hasattr(stop_result, 'data') and stop_result.data else 0,
            'stoppedAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        msg=stop_result.message
    )


@chatMessageController.post('/{message_id}/regenerate')  # 移除权限检查
async def regenerate_message(
    request: Request,
    message_id: str,
    regenerate_message: RegenerateMessageModel,
    query_db: AsyncSession = Depends(get_db),
):  # 移除 current_user 依赖
    """
    重新生成消息

    :param message_id: 消息ID（UUID，用户消息）
    :param regenerate_message: 重新生成参数
    :return: SSE流
    """
    DEBUG_USER_ID = 1

    # 获取用户消息ID和相关信息
    user_message_id, conversation_id, model_id, messages = await ChatMessageService.regenerate_message_services(
        query_db, message_id, regenerate_message, DEBUG_USER_ID
    )

    # 生成临时 AI 消息 ID（使用UUID）
    assistant_message_id = generate_uuid()

    async def generate_regenerate_stream():
        """生成重新生成的流式响应"""
        try:
            # 获取 DeepSeek 客户端
            deepseek_client = get_deepseek_client()

            # 发送 message_start 事件（包含完整的消息 ID 信息）
            yield f"event: message_start\ndata: {json.dumps({'userMessageId': user_message_id, 'assistantMessageId': assistant_message_id, 'conversationId': conversation_id})}\n\n"

            # 准备响应内容
            response_content = ""
            thinking_content = ""
            final_message_id = None

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
                    await asyncio.sleep(0)

                elif event_type == "thinking_delta":
                    thinking_content += event_data.get("content", "")
                    yield f"event: thinking_delta\ndata: {json.dumps({'content': event_data.get('content', '')})}\n\n"
                    await asyncio.sleep(0)

                elif event_type == "thinking_end":
                    yield f"event: thinking_end\ndata: {json.dumps({})}\n\n"
                    await asyncio.sleep(0)

                elif event_type == "content_delta":
                    response_content += event_data.get("content", "")
                    yield f"event: content_delta\ndata: {json.dumps({'content': event_data.get('content', '')})}\n\n"
                    await asyncio.sleep(0)  # 关键：确保每次 yield 后立即发送数据

                elif event_type == "message_end":
                    # 创建助手消息记录（使用新的数据库会话，避免连接超时）
                    async with AsyncSessionLocal() as new_db:
                        final_message_id = await ChatMessageService.replace_assistant_message_services(
                            new_db,
                            conversation_id,
                            response_content,
                            thinking_content if thinking_content else None,
                            event_data.get("tokens_used", 0),
                        )

                        # 发送结束事件（包含完整消息信息）
                        yield f"event: message_end\ndata: {json.dumps({'messageId': final_message_id, 'content': response_content, 'thinkingContent': thinking_content if thinking_content else None, 'tokensUsed': event_data.get('tokens_used', 0), 'totalTokens': event_data.get('total_tokens', 0)})}\n\n"
                        await asyncio.sleep(0)
                    break

        except Exception as e:
            logger.error(f'重新生成失败: {str(e)}')
            yield f"event: error\ndata: {json.dumps({'code': 1009, 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_regenerate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 禁用nginx缓冲
            "Connection": "keep-alive",
        }
    )
