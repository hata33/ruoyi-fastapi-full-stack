"""
测试新增的消息管理接口
测试：停止生成、重新生成、获取消息列表
"""
import httpx
import asyncio
import json


async def test():
    async with httpx.AsyncClient(timeout=120.0) as client:
        # 1. 登录
        print("=== 1. 登录 ===")
        login = await client.post(
            "http://localhost:9099/login",
            data={"username": "admin", "password": "admin@123", "code": "1234"}
        )
        login_data = login.json()
        print(f"登录响应: {login_data}")
        if login_data.get("code") != 200:
            print(f"登录失败: {login_data.get('msg')}")
            return
        token = login_data["data"]["token"]
        print(f"Token: {token[:30]}...")
        headers = {"Authorization": f"Bearer {token}"}

        # 2. 创建会话
        print("\n=== 2. 创建测试会话 ===")
        conv = await client.post(
            "http://localhost:9099/api/chat/conversations",
            headers=headers,
            json={"title": "消息测试会话", "modelId": "deepseek-chat"}
        )
        conversation_id = conv.json()["data"]["conversation_id"]
        print(f"会话ID: {conversation_id}")

        # 3. 获取消息列表（空会话）
        print("\n=== 3. 获取消息列表（空会话） ===")
        list_resp = await client.get(
            f"http://localhost:9099/api/chat/conversations/{conversation_id}/messages",
            headers=headers,
            params={"page_size": 50}
        )
        print(f"状态码: {list_resp.status_code}")
        result = list_resp.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False)[:500]}")

        if result.get("code") == 200:
            data = result.get("data", {})
            rows = data.get("rows", []) if isinstance(data, dict) else []
            total = data.get("total", 0) if isinstance(data, dict) else 0
            has_more = data.get("hasMore", False) if isinstance(data, dict) else False
            print(f"[PASS] 获取消息列表成功")
            print(f"   消息数量: {len(rows)}/{total}")
            print(f"   是否有更多: {has_more}")
        else:
            print(f"[FAIL] 获取消息列表失败: {result.get('msg')}")

        # 4. 发送一条消息
        print("\n=== 4. 发送消息 ===")
        send_resp = await client.post(
            "http://localhost:9099/api/chat/messages/stream",
            headers=headers,
            json={
                "conversationId": conversation_id,
                "content": "请简单介绍一下Python"
            }
        )
        print(f"状态码: {send_resp.status_code}")

        # 注意：流式响应需要特殊处理，这里只记录状态
        if send_resp.status_code == 200:
            print("[PASS] 消息发送成功（流式）")

        # 5. 再次获取消息列表
        print("\n=== 5. 再次获取消息列表 ===")
        list_resp2 = await client.get(
            f"http://localhost:9099/api/chat/conversations/{conversation_id}/messages",
            headers=headers,
            params={"page_size": 50}
        )
        result2 = list_resp2.json()

        if result2.get("code") == 200:
            data = result2.get("data", {})
            rows = data.get("rows", []) if isinstance(data, dict) else []
            total = data.get("total", 0) if isinstance(data, dict) else 0
            print(f"[PASS] 获取消息列表成功")
            print(f"   消息数量: {len(rows)}/{total}")

            if rows:
                for msg in rows[:3]:
                    if isinstance(msg, dict):
                        role = msg.get("role")
                        content_preview = msg.get("content", "")[:50]
                        if len(msg.get("content", "")) > 50:
                            content_preview += "..."
                        print(f"   - {role}: {content_preview}")

                # 6. 测试重新生成（找到第一条用户消息）
                print("\n=== 6. 测试重新生成 ===")
                user_msg_id = None
                for msg in rows:
                    if isinstance(msg, dict) and msg.get("role") == "user":
                        user_msg_id = msg.get("messageId")
                        break

                if user_msg_id:
                    print(f"用户消息ID: {user_msg_id}")
                    regen_resp = await client.post(
                        f"http://localhost:9099/api/chat/messages/{user_msg_id}/regenerate",
                        headers=headers,
                        json={"modelId": "deepseek-chat"}
                    )
                    print(f"重新生成状态码: {regen_resp.status_code}")
                    # 重新生成返回 SSE 流，这里只检查状态
                    if regen_resp.status_code == 200:
                        print("[PASS] 重新生成接口调用成功（返回 SSE 流）")
                    else:
                        print(f"[FAIL] 重新生成失败: {regen_resp.text[:200]}")
                else:
                    print("[SKIP] 没有找到用户消息，跳过重新生成测试")

        # 7. 测试停止生成
        print("\n=== 7. 测试停止生成 ===")
        # 使用第一条消息ID测试停止功能
        if result2.get("code") == 200:
            data = result2.get("data", {})
            rows = data.get("rows", []) if isinstance(data, dict) else []
            if rows:
                test_msg_id = rows[0].get("messageId") if isinstance(rows[0], dict) else None
                if test_msg_id:
                    stop_resp = await client.post(
                        f"http://localhost:9099/api/chat/messages/{test_msg_id}/stop",
                        headers=headers
                    )
                    print(f"停止生成状态码: {stop_resp.status_code}")
                    stop_result = stop_resp.json()
                    print(f"响应: {stop_result}")
                    if stop_result.get("code") == 200:
                        print("[PASS] 停止生成接口正常")
                    else:
                        print(f"[FAIL] 停止生成失败: {stop_result.get('msg')}")

        print("\n=== 测试完成 ===")


if __name__ == "__main__":
    asyncio.run(test())
