"""
测试 DeepSeek 客户端（直接测试，无需认证）

测试编号: 06
测试类型: 单元测试
测试模块: DeepSeek Client
运行方式：
python tests/chat/06_test_deepseek_client.py

测试内容：
1. 模拟模式测试（无 API Key）
2. Reasoner 模型测试（推理模式）
3. 真实 API 测试（需要配置 API Key）
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from module_chat.service.deepseek_client import DeepSeekClient
from utils.log_util import logger


async def test_mock_mode():
    """测试模拟模式（无 API Key）"""
    print("="*60)
    print("测试 DeepSeek 客户端 - 模拟模式")
    print("="*60)

    client = DeepSeekClient()

    messages = [
        {"role": "user", "content": "你好，请用一句话介绍你自己"}
    ]

    print(f"\n发送消息: {messages[0]['content']}")
    print(f"\n流式响应:\n")
    print("-"*60)

    try:
        full_content = ""
        event_count = 0

        async for event in client.chat_stream(messages=messages, model="deepseek-chat"):
            event_type = event.get("event")
            event_data = event.get("data", {})

            event_count += 1

            if event_type == "message_start":
                print(f"[事件 {event_count}] 消息开始")

            elif event_type == "content_delta":
                content = event_data.get("content", "")
                full_content += content
                print(content, end="", flush=True)

            elif event_type == "message_end":
                tokens = event_data.get("tokens_used", 0)
                print(f"\n\n[事件 {event_count}] 消息结束")
                print(f"使用 tokens: {tokens}")
                print(f"完整回复长度: {len(full_content)} 字符")
                print("-"*60)
                print(f"\n测试完成!")
                return True

        return False

    except Exception as e:
        print(f"\n测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_with_api_key():
    """测试真实 API（如果有 API Key）"""
    # 从环境变量或配置文件读取 API Key
    api_key = os.getenv("DEEPSEEK_API_KEY", "")

    if not api_key:
        print("未配置 DEEPSEEK_API_KEY 环境变量，跳过真实 API 测试")
        return False

    print("="*60)
    print("测试 DeepSeek 客户端 - 真实 API")
    print("="*60)

    # 临时设置 API Key
    from config.env import DeepSeekConfig
    DeepSeekConfig.deepseek_api_key = api_key

    client = DeepSeekClient()

    messages = [
        {"role": "user", "content": "你好，请用一句话介绍你自己"}
    ]

    print(f"\nAPI Base: {client.api_base}")
    print(f"发送消息: {messages[0]['content']}")
    print(f"\n流式响应:\n")
    print("-"*60)

    try:
        full_content = ""
        event_count = 0

        async for event in client.chat_stream(messages=messages, model="deepseek-chat"):
            event_type = event.get("event")
            event_data = event.get("data", {})

            event_count += 1

            if event_type == "message_start":
                print(f"[事件 {event_count}] 消息开始")

            elif event_type == "content_delta":
                content = event_data.get("content", "")
                full_content += content
                print(content, end="", flush=True)

            elif event_type == "message_end":
                tokens = event_data.get("tokens_used", 0)
                print(f"\n\n[事件 {event_count}] 消息结束")
                print(f"使用 tokens: {tokens}")
                print(f"完整回复长度: {len(full_content)} 字符")
                print("-"*60)
                print(f"\n真实 API 测试完成!")
                return True

        return False

    except Exception as e:
        print(f"\n真实 API 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_reasoner_model():
    """测试 reasoner 模型"""
    print("\n" + "="*60)
    print("测试 DeepSeek Reasoner 模型（推理模式）")
    print("="*60)

    client = DeepSeekClient()

    messages = [
        {"role": "user", "content": "1+1等于几？请推理一下"}
    ]

    print(f"\n发送消息: {messages[0]['content']}")
    print(f"\n流式响应:\n")
    print("-"*60)

    try:
        thinking_content = ""
        response_content = ""
        event_count = 0

        async for event in client.chat_stream(messages=messages, model="deepseek-reasoner"):
            event_type = event.get("event")
            event_data = event.get("data", {})

            event_count += 1

            if event_type == "message_start":
                print(f"[事件 {event_count}] 消息开始")

            elif event_type == "thinking_start":
                print(f"[事件 {event_count}] 推理开始")

            elif event_type == "thinking_delta":
                content = event_data.get("content", "")
                thinking_content += content
                print(f"[推理] {content}", end="", flush=True)

            elif event_type == "thinking_end":
                print(f"\n[事件 {event_count}] 推理结束")

            elif event_type == "content_delta":
                content = event_data.get("content", "")
                response_content += content
                print(f"[回复] {content}", end="", flush=True)

            elif event_type == "message_end":
                tokens = event_data.get("tokens_used", 0)
                print(f"\n\n[事件 {event_count}] 消息结束")
                print(f"推理内容: {len(thinking_content)} 字符")
                print(f"回复内容: {len(response_content)} 字符")
                print(f"使用 tokens: {tokens}")
                print("-"*60)
                print(f"\nReasoner 模型测试完成!")
                return True

        return False

    except Exception as e:
        print(f"\nReasoner 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("DeepSeek 客户端测试套件")
    print("="*60)

    # 测试 1: 模拟模式
    success1 = await test_mock_mode()

    # 测试 2: Reasoner 模型
    success2 = await test_reasoner_model()

    # 测试 3: 真实 API（如果配置了）
    success3 = await test_with_api_key()

    # 总结
    print("\n" + "="*60)
    print("测试总结:")
    print("="*60)
    print(f"模拟模式: {'✓ 通过' if success1 else '✗ 失败'}")
    print(f"Reasoner 模型: {'✓ 通过' if success2 else '✗ 失败'}")
    print(f"真实 API: {'✓ 通过' if success3 else '✗ 跳过'}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
