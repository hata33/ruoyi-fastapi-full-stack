"""测试后端是否真的在流式输出"""
import asyncio
import httpx
import time
import json

async def test_stream():
    print("=== 测试后端流式输出 ===\n")

    async with httpx.AsyncClient(timeout=120.0) as client:
        # 1. 登录
        print("1. 登录中...")
        login = await client.post(
            "http://localhost:9099/login",
            data={"username": "admin", "password": "admin@123", "code": "1234"}
        )
        login_data = login.json()

        if login_data.get("code") != 200:
            print(f"   登录失败: {login_data}")
            return

        # 登录响应中 token 直接在根级别
        token = login_data.get("token")
        if not token:
            print(f"   登录响应中没有 token: {login_data}")
            return

        print(f"[OK] 登录成功\n")

        # 2. 创建会话
        print("2. 创建会话...")
        conv = await client.post(
            "http://localhost:9099/api/chat/conversations",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "测试流式", "modelId": "deepseek-chat"}
        )
        conv_data = conv.json()
        print(f"   会话响应: {conv_data}")

        if conv_data.get("code") != 200:
            print(f"创建会话失败: {conv_data}")
            return

        conversation_id = conv_data["data"]["conversationId"]  # 注意大小写
        print(f"[OK] 创建会话: {conversation_id}\n")

        # 3. 测试流式消息
        print("3. 测试流式消息...")
        print(f"   发送时间: {time.time()}")
        start_time = time.time()

        try:
            async with client.stream(
                "POST",
                "http://localhost:9099/api/chat/messages/stream",
                headers={"Authorization": f"Bearer {token}"},
                json={"conversationId": conversation_id, "content": "1+1等于几？"}
            ) as response:
                print(f"   状态码: {response.status_code}")
                print(f"   Content-Type: {response.headers.get('content-type')}\n")

                if response.status_code != 200:
                    print(f"请求失败: {await response.aread()}")
                    return

                event_count = 0
                content_events = 0
                last_event_time = start_time

                print("   接收事件:")
                async for line in response.aiter_lines():
                    if line.strip():
                        current_time = time.time()
                        elapsed = current_time - start_time
                        elapsed_from_last = current_time - last_event_time
                        event_count += 1
                        last_event_time = current_time

                        if "event:" in line:
                            event_type = line.split(":", 1)[1].strip()
                            if event_type in ["content_delta", "thinking_delta", "message_start", "message_end"]:
                                if event_type == "content_delta":
                                    content_events += 1
                                print(f"   [{elapsed:.3f}s] (+{elapsed_from_last:.3f}s) {event_type}")

                        if line.startswith("data:"):
                            try:
                                data_str = line[5:].strip()
                                data = json.loads(data_str)
                                if "messageId" in data:
                                    print(f"\n   === 完成 ===")
                                    print(f"   总事件数: {event_count}")
                                    print(f"   内容事件数: {content_events}")
                                    print(f"   总耗时: {elapsed:.3f} 秒")
                                    return
                            except:
                                pass

        except Exception as e:
            print(f"   错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_stream())
