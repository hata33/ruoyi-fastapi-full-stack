"""
DeepSeek API 客户端

说明：
- 封装 DeepSeek API 调用
- 支持流式响应
- 支持 deepseek-chat 和 deepseek-reasoner 模型
"""

import json
import httpx
from typing import AsyncGenerator, Optional
from utils.log_util import logger
from config.env import AppConfig


class DeepSeekClient:
    """DeepSeek API 客户端"""

    # 支持的模型
    MODEL_CHAT = "deepseek-chat"
    MODEL_REASONER = "deepseek-reasoner"

    def __init__(self):
        """初始化客户端"""
        from config.env import DeepSeekConfig

        self.api_key = DeepSeekConfig.deepseek_api_key
        self.api_base = DeepSeekConfig.deepseek_api_base
        self.timeout = DeepSeekConfig.deepseek_timeout
        self.max_retries = DeepSeekConfig.deepseek_max_retries

        # API 端点
        self.CHAT_ENDPOINT = f"{self.api_base}/chat/completions"

        if not self.api_key:
            logger.warning("DEEPSEEK_API_KEY 未配置，将使用模拟模式")

    async def _make_request(self, messages: list, model: str, stream: bool = True, **kwargs) -> AsyncGenerator:
        """
        发起 API 请求

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

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
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
                            except json.JSONDecodeError:
                                continue
                else:
                    data = response.json()
                    yield data

            except httpx.HTTPStatusError as e:
                logger.error(f"DeepSeek API 请求失败: {e.response.status_code} - {e.response.text}")
                raise Exception(f"AI 服务请求失败: {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"DeepSeek API 网络错误: {str(e)}")
                raise Exception(f"AI 服务网络错误: {str(e)}")
            except Exception as e:
                logger.error(f"DeepSeek API 未知错误: {str(e)}")
                raise Exception(f"AI 服务错误: {str(e)}")

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

        # 发送消息开始事件
        yield {"event": "message_start", "data": {}}

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
                tokens_used = usage.get("total_tokens", 0)

                yield {
                    "event": "message_end",
                    "data": {
                        "thinking_content": thinking_content if is_reasoner else None,
                        "content": response_content,
                        "tokens_used": tokens_used,
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
