"""
置顶和标签管理测试
"""
import httpx
import asyncio
import random


async def test():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 登录
        print("=== 登录 ===")
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
        headers = {"Authorization": f"Bearer {token}"}

        # 创建测试会话
        print("=== 创建测试会话 ===")
        conv = await client.post(
            "http://localhost:9099/api/chat/conversations",
            headers=headers,
            json={"title": "置顶测试会话", "modelId": "deepseek-chat"}
        )
        conv_id = conv.json()["data"]["conversation_id"]
        print(f"会话ID: {conv_id}")

        # ========== 置顶测试 ==========

        # 1. 置顶会话
        print("\n=== 1. 置顶会话 ===")
        pin_resp = await client.put(
            f"http://localhost:9099/api/chat/conversations/{conv_id}/pin",
            headers=headers,
            json={"isPinned": True}
        )
        print(f"状态码: {pin_resp.status_code}")
        print(f"响应: {pin_resp.json()}")
        if pin_resp.json().get("code") == 200:
            print("[PASS] 置顶成功")

        # 2. 验证置顶效果
        print("\n=== 2. 验证置顶效果 ===")
        list_resp = await client.get(
            "http://localhost:9099/api/chat/conversations",
            headers=headers,
            params={"page_num": 1, "page_size": 5}
        )
        rows = list_resp.json().get("rows", [])
        if rows:
            first = rows[0]
            if first.get("isPinned") and first.get("conversationId") == conv_id:
                print(f"[PASS] 置顶会话排第一: {first.get('title')}")
            else:
                print(f"[WARN] 第一条: {first.get('title')}, is_pinned={first.get('isPinned')}")

        # 3. 取消置顶
        print("\n=== 3. 取消置顶 ===")
        unpin_resp = await client.put(
            f"http://localhost:9099/api/chat/conversations/{conv_id}/pin",
            headers=headers,
            json={"isPinned": False}
        )
        print(f"状态码: {unpin_resp.status_code}")
        print(f"响应: {unpin_resp.json()}")
        if unpin_resp.json().get("code") == 200:
            print("[PASS] 取消置顶成功")

        # ========== 标签测试 ==========

        # 4. 创建标签
        print("\n=== 4. 创建标签 ===")
        tag_name = f"测试标签_{random.randint(1000, 9999)}"
        tag_resp = await client.post(
            "http://localhost:9099/api/chat/tags",
            headers=headers,
            json={"tagName": tag_name, "tagColor": "#1890ff"}
        )
        print(f"状态码: {tag_resp.status_code}")
        tag_result = tag_resp.json()
        print(f"响应: {tag_result}")
        if tag_result.get("code") == 200:
            print("[PASS] 创建标签成功")
            tag_id = tag_result["data"]["tag_id"]

            # 5. 获取标签列表
            print("\n=== 5. 获取标签列表 ===")
            tags_resp = await client.get(
                "http://localhost:9099/api/chat/tags",
                headers=headers
            )
            tags = tags_resp.json().get("data", [])
            print(f"标签数量: {len(tags)}")
            for tag in tags:
                print(f"   - {tag.get('tagName')} ({tag.get('tagColor')})")

            # 6. 删除标签
            print("\n=== 6. 删除标签 ===")
            del_resp = await client.delete(
                f"http://localhost:9099/api/chat/tags/{tag_id}",
                headers=headers
            )
            print(f"状态码: {del_resp.status_code}")
            print(f"响应: {del_resp.json()}")
            if del_resp.json().get("code") == 200:
                print("[PASS] 删除标签成功")


if __name__ == "__main__":
    asyncio.run(test())
