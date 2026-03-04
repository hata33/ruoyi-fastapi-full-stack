"""
DeepSeek API 客户端

说明：
- 封装 DeepSeek API 调用
- 支持流式响应
- 支持 deepseek-chat 和 deepseek-reasoner 模型
- 添加请求重试机制
"""

import asyncio
import json
from typing import AsyncGenerator, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.env import AppConfig
from utils.log_util import logger


class DeepSeekClient:
    """DeepSeek API 客户端"""

    # 支持的模型
    MODEL_CHAT = "deepseek-chat"
    MODEL_REASONER = "deepseek-reasoner"

    # 重试配置
    MAX_RETRIES = 3  # 最大重试次数
    INITIAL_RETRY_DELAY = 1.0  # 初始重试延迟（秒）
    MAX_RETRY_DELAY = 10.0  # 最大重试延迟（秒）

    def __init__(self):
        """初始化客户端"""
        from config.env import DeepSeekConfig

        self.api_key = DeepSeekConfig.deepseek_api_key
        self.api_base = DeepSeekConfig.deepseek_api_base
        self.timeout = DeepSeekConfig.deepseek_timeout
        self.max_retries = DeepSeekConfig.deepseek_max_retries if hasattr(DeepSeekConfig, 'deepseek_max_retries') else self.MAX_RETRIES

        # API 端点
        self.CHAT_ENDPOINT = f"{self.api_base}/chat/completions"

        if not self.api_key:
            logger.warning("DEEPSEEK_API_KEY 未配置，将使用模拟模式")

    def _is_retryable_error(self, error: Exception) -> bool:
        """
        判断错误是否可以重试

        :param error: 异常对象
        :return: 是否可重试
        """
        # 网络相关错误可以重试
        if isinstance(error, (httpx.RequestError, httpx.RemoteProtocolError)):
            return True

        # HTTP 5xx 服务器错误可以重试
        if isinstance(error, httpx.HTTPStatusError):
            return 500 <= error.response.status_code < 600

        # 超时错误可以重试
        if isinstance(error, (httpx.TimeoutException, asyncio.TimeoutError)):
            return True

        return False

    async def _make_request(self, messages: list, model: str, stream: bool = True, **kwargs) -> AsyncGenerator:
        """
        发起 API 请求（带重试机制）

        :param messages: 消息列表
        :param model: 模型名称
        :param stream: 是否流式响应
        :param kwargs: 其他参数（temperature, max_tokens 等）
        :yield: 响应片段
        """
        if not self.api_key:
            # 如果没有配置 API Key，使用模拟模式
            async for chunk in self._mock_stream(messages, model):
                yield chunk
            return

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs
        }

        # 重试逻辑
        last_error = None
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.CHAT_ENDPOINT,
                        headers=headers,
                        json=payload
                    )
                    response.raise_for_status()

                    if stream:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:]
                                if data_str == "[DONE]":
                                    break
                                try:
                                    yield json.loads(data_str)
                                except json.JSONDecodeError as e:
                                    logger.warning(f"JSON解析失败: {e}")
                                    continue
                    else:
                        data = response.json()
                        yield data

                    # 成功则退出重试循环
                    return

            except Exception as e:
                last_error = e
                is_retryable = self._is_retryable_error(e)

                if not is_retryable:
                    # 不可重试的错误直接抛出
                    logger.error(f"DeepSeek API 不可重试错误: {str(e)}")
                    raise

                if attempt < self.max_retries - 1:
                    # 计算重试延迟（指数退避）
                    delay = min(
                        self.INITIAL_RETRY_DELAY * (2 ** attempt),
                        self.MAX_RETRY_DELAY
                    )
                    logger.warning(
                        f"DeepSeek API 请求失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}"
                        f"，{delay}秒后重试..."
                    )
                    await asyncio.sleep(delay)
                else:
                    # 最后一次尝试仍然失败
                    logger.error(f"DeepSeek API 请求失败，已达最大重试次数: {str(e)}")
                    raise Exception(f"AI 服务请求失败: {str(e)}")

    async def _mock_stream(self, messages: list, model: str) -> AsyncGenerator:
        """
        模拟流式响应（用于测试）

        :param messages: 消息列表
        :param model: 模型名称
        :yield: 模拟的响应片段
        """
        user_message = messages[-1].get("content", "") if messages else ""

        # 模拟推理过程
        if model == self.MODEL_REASONER:
            yield {
                "choices": [{
                    "delta": {"role": "assistant", "content": ""},
                    "finish_reason": None
                }]
            }

        # 模拟回复内容
        mock_response = f"这是对'{user_message[:50]}...'的模拟回复。\n\n在实际部署中，这里会调用 DeepSeek API 生成真实的 AI 回复内容。"

        for char in mock_response:
            yield {
                "choices": [{
                    "delta": {"content": char},
                    "finish_reason": None
                }]
            }

        # 结束标记
        yield {
            "choices": [{
                "delta": {},
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(str(messages)),
                "completion_tokens": len(mock_response),
                "total_tokens": len(str(messages)) + len(mock_response)
            }
        }

    async def chat_stream(
        self,
        messages: list,
        model: str = MODEL_CHAT,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        流式聊天接口

        :param messages: 消息列表，格式 [{"role": "user", "content": "..."}]
        :param model: 模型名称（deepseek-chat 或 deepseek-reasoner）
        :param temperature: 温度参数（0-2），越高越随机
        :param top_p: 采样参数（0-1）
        :param max_tokens: 最大生成 token 数
        :yield: SSE 事件数据
        """
        # 构建请求参数
        kwargs = {}
        if temperature is not None:
            kwargs["temperature"] = temperature
        if top_p is not None:
            kwargs["top_p"] = top_p
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        # reasoner 模型特殊处理
        is_reasoner = model == self.MODEL_REASONER

        # 注意：message_start 事件由 controller 层发送（包含消息ID等元数据）
        # 如果是 reasoner 模型，发送推理开始事件
        if is_reasoner:
            yield {"event": "thinking_start", "data": {}}

        thinking_content = ""
        response_content = ""

        async for chunk in self._make_request(messages, model, stream=True, **kwargs):
            if not chunk.get("choices"):
                continue

            choice = chunk["choices"][0]
            delta = choice.get("delta", {})
            finish_reason = choice.get("finish_reason")

            # 处理推理过程（reasoner 模型特有）
            if "reasoning_content" in delta or "reasoning" in delta:
                reasoning = delta.get("reasoning_content") or delta.get("reasoning", "")
                if reasoning:
                    thinking_content += reasoning
                    yield {
                        "event": "thinking_delta",
                        "data": {"content": reasoning}
                    }
                continue

            # 处理普通内容
            content = delta.get("content", "")
            if content:
                response_content += content
                yield {
                    "event": "content_delta",
                    "data": {"content": content}
                }

            # 检查是否完成
            if finish_reason:
                # 如果是 reasoner 模型，发送推理结束事件
                if is_reasoner and thinking_content:
                    yield {"event": "thinking_end", "data": {}}

                # 获取 token 使用情况
                usage = chunk.get("usage", {})
                total_tokens = usage.get("total_tokens", 0)

                # 发送结束事件（token统计信息，controller需要这些数据）
                yield {
                    "event": "message_end",
                    "data": {
                        "tokens_used": total_tokens,
                        "total_tokens": total_tokens,
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                    }
                }
                break

    def is_reasoner_model(self, model: str) -> bool:
        """
        判断是否为 reasoner 模型

        :param model: 模型名称
        :return: 是否为 reasoner 模型
        """
        return model == self.MODEL_REASONER or "reasoner" in model.lower()


# 全局客户端实例
_deepseek_client: Optional[DeepSeekClient] = None


def get_deepseek_client() -> DeepSeekClient:
    """
    获取 DeepSeek 客户端实例（单例模式）

    :return: DeepSeek 客户端实例
    """
    global _deepseek_client
    if _deepseek_client is None:
        _deepseek_client = DeepSeekClient()
    return _deepseek_client
