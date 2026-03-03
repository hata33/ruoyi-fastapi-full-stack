"""
测试 DeepSeek 流式数据接口（完整端到端测试）

测试编号: 08
测试类型: 端到端测试
测试模块: Chat Stream API
运行方式：
1. 确保后端服务正在运行
2. 运行此脚本：python tests/chat/08_test_deepseek_stream.py

测试内容：
1. 用户登录认证
2. 创建聊天会话
3. 发送消息并接收流式响应
4. 验证 SSE 事件格式
"""

import asyncio
import httpx
import json
from typing import AsyncGenerator


# 配置
BASE_URL = "http://localhost:9099"
USERNAME = "admin"
PASSWORD = "admin123"


async def login() -> str:
    """登录并获取 token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/login",
            data={
                "username": USERNAME,
                "password": PASSWORD,
                "code": "1234",
                "uuid": "test-uuid"
            }
        )
        result = response.json()
        if result.get("code") == 200:
            print(f"✓ 登录成功")
            return result.get("data", {}).get("token")
        else:
            print(f"✗ 登录失败: {result.get('msg')}")
            raise Exception("登录失败")


async def create_conversation(token: str) -> int:
    """创建测试会话"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/chat/conversations",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "测试会话",
                "modelId": "deepseek-chat"
            }
        )
        result = response.json()
        if result.get("code") == 200:
            conversation_id = result.get("data", {}).get("conversationId")
            print(f"✓ 创建会话成功，ID: {conversation_id}")
            return conversation_id
        else:
            print(f"✗ 创建会话失败: {result.get('msg')}")
            raise Exception("创建会话失败")


async def test_stream_message(token: str, conversation_id: int):
    """测试流式消息"""
    print(f"\n开始测试流式消息...")
    print(f"会话 ID: {conversation_id}")
    print(f"发送消息: 你好，请用一句话介绍你自己")
    print(f"\n{'='*60}")
    print(f"流式响应:")
    print(f"{'='*60}\n")

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async with client.stream(
                "POST",
                f"{BASE_URL}/api/chat/messages/stream",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "conversationId": conversation_id,
                    "content": "你好，请用一句话介绍你自己",
                    "modelId": "deepseek-chat"
                }
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    print(f"✗ 请求失败: {response.status_code}")
                    print(f"错误详情: {error_text.decode()}")
                    return

                full_content = ""
                event_count = 0

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    # 解析 SSE 格式
                    if line.startswith("event:"):
                        event_type = line[6:].strip()
                        continue
                    elif line.startswith("data:"):
                        data_str = line[5:].strip()
                        try:
                            data = json.loads(data_str)
                            event_count += 1

                            # 处理不同事件
                            if "messageId" in data:
                                print(f"[事件 {event_count}] message_start: 消息ID = {data['messageId']}")
                            elif "content" in data:
                                content = data["content"]
                                full_content += content
                                print(content, end="", flush=True)
                            elif "tokens_used" in data:
                                tokens = data["tokens_used"]
                                print(f"\n\n[事件 {event_count}] message_end: 使用了 {tokens} 个 token")
                                print(f"\n完整回复长度: {len(full_content)} 字符")
                                print(f"{'='*60}\n")
                                print(f"✓ 流式测试完成")
                                return

                        except json.JSONDecodeError as e:
                            print(f"\n✗ JSON 解析失败: {data_str}")
                            continue

        except Exception as e:
            print(f"\n✗ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()


async def main():
    """主测试流程"""
    print("="*60)
    print("DeepSeek 流式数据测试")
    print("="*60)

    try:
        # 1. 登录
        print(f"\n1. 登录系统...")
        token = await login()

        # 2. 创建会话
        print(f"\n2. 创建测试会话...")
        conversation_id = await create_conversation(token)

        # 3. 测试流式消息
        print(f"\n3. 测试流式消息...")
        await test_stream_message(token, conversation_id)

    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
