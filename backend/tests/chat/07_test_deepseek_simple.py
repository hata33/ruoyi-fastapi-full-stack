"""
测试 DeepSeek 流式数据接口（简化版）

测试编号: 07
测试类型: 集成测试
测试模块: DeepSeek Stream
运行方式：
python tests/chat/07_test_deepseek_simple.py

测试内容：
1. 基本流式输出测试
2. Reasoner 模型推理测试
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from module_chat.service.deepseek_client import DeepSeekClient


async def test_basic_stream():
    """测试基本流式功能"""
    print("Testing DeepSeek Client Stream...")
    print("="*50)

    client = DeepSeekClient()

    # 测试 1: 普通模型
    print("\nTest 1: DeepSeek Chat Model")
    print("-"*50)

    messages = [{"role": "user", "content": "What is 2+2?"}]

    try:
        full_content = ""
        async for event in client.chat_stream(messages=messages, model="deepseek-chat"):
            event_type = event.get("event")
            event_data = event.get("data", {})

            if event_type == "message_start":
                print("[Start] Message started")

            elif event_type == "content_delta":
                content = event_data.get("content", "")
                full_content += content
                print(content, end="", flush=True)

            elif event_type == "message_end":
                tokens = event_data.get("tokens_used", 0)
                print(f"\n[End] Tokens used: {tokens}")
                print(f"Content length: {len(full_content)} chars")
                break

        print("Test 1: PASSED\n")

    except Exception as e:
        print(f"Test 1: FAILED - {str(e)}\n")

    # 测试 2: Reasoner 模型
    print("Test 2: DeepSeek Reasoner Model")
    print("-"*50)

    messages = [{"role": "user", "content": "Solve: 1+1"}]

    try:
        thinking = ""
        response = ""
        async for event in client.chat_stream(messages=messages, model="deepseek-reasoner"):
            event_type = event.get("event")
            event_data = event.get("data", {})

            if event_type == "thinking_start":
                print("[Start] Thinking started")

            elif event_type == "thinking_delta":
                content = event_data.get("content", "")
                thinking += content
                # Don't print thinking to avoid encoding issues

            elif event_type == "thinking_end":
                print(f"[End] Thinking completed ({len(thinking)} chars)")

            elif event_type == "content_delta":
                content = event_data.get("content", "")
                response += content
                print(content, end="", flush=True)

            elif event_type == "message_end":
                tokens = event_data.get("tokens_used", 0)
                print(f"\n[End] Tokens used: {tokens}")
                print(f"Response length: {len(response)} chars")
                break

        print("Test 2: PASSED\n")

    except Exception as e:
        print(f"Test 2: FAILED - {str(e)}\n")

    print("="*50)
    print("All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_basic_stream())
