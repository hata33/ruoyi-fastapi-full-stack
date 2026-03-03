"""
完整流程测试
模拟用户真实使用场景
"""
import httpx
import asyncio
import random


async def test():
    async with httpx.AsyncClient(timeout=60.0) as client:
        # ============ 登录 ============
        print(">>> 登录系统")
        login = await client.post(
            "http://localhost:9099/login",
            data={"username": "admin", "password": "admin123", "code": "1234"}
        )
        token = login.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ 登录成功")

        # ============ 创建多个会话 ============
        print("\n>>> 创建3个测试会话")
        conv_ids = []
        titles = ["工作计划", "学习笔记", "项目讨论"]
        for title in titles:
            resp = await client.post(
                "http://localhost:9099/api/chat/conversations",
                headers=headers,
                json={"title": title, "modelId": "deepseek-chat"}
            )
            if resp.json().get("code") == 200:
                conv_id = resp.json()["data"]["conversation_id"]
                conv_ids.append((conv_id, title))
                print(f"   ✅ 创建会话: {title} (ID: {conv_id})")

        # ============ 查看会话列表 ============
        print("\n>>> 查看会话列表")
        resp = await client.get(
            "http://localhost:9099/api/chat/conversations",
            headers=headers,
            params={"page_num": 1, "page_size": 10}
        )
        rows = resp.json().get("rows", [])
        print(f"   共有 {len(rows)} 个会话")
        for row in rows[:3]:
            print(f"   - {row.get('title')} (置顶: {row.get('isPinned')})")

        # ============ 置顶重要会话 ============
        print("\n>>> 置顶第一个会话")
        if conv_ids:
            conv_id, _ = conv_ids[0]
            resp = await client.put(
                f"http://localhost:9099/api/chat/conversations/{conv_id}/pin",
                headers=headers,
                json={"isPinned": True}
            )
            if resp.json().get("code") == 200:
                print(f"   ✅ 已置顶: {conv_ids[0][1]}")

        # ============ 创建分类标签 ============
        print("\n>>> 创建分类标签")
        tags = [
            {"tagName": "重要", "tagColor": "#ff4d4f"},
            {"tagName": "待处理", "tagColor": "#faad14"}
        ]
        tag_ids = []
        for tag in tags:
            # 使用随机名称避免重复
            tag["tagName"] = f"{tag['tagName']}_{random.randint(100, 999)}"
            resp = await client.post(
                "http://localhost:9099/api/chat/tags",
                headers=headers,
                json=tag
            )
            if resp.json().get("code") == 200:
                tag_id = resp.json()["data"]["tag_id"]
                tag_ids.append(tag_id)
                print(f"   ✅ 创建标签: {tag['tagName']}")

        # ============ 查看所有标签 ============
        print("\n>>> 查看所有标签")
        resp = await client.get(
            "http://localhost:9099/api/chat/tags",
            headers=headers
        )
        all_tags = resp.json().get("data", [])
        print(f"   共有 {len(all_tags)} 个标签")

        # ============ 清理测试数据 ============
        print("\n>>> 清理测试数据")
        # 删除标签
        for tag_id in tag_ids:
            await client.delete(
                f"http://localhost:9099/api/chat/tags/{tag_id}",
                headers=headers
            )
        print(f"   ✅ 删除 {len(tag_ids)} 个标签")

        # 删除会话
        for conv_id, _ in conv_ids:
            await client.delete(
                f"http://localhost:9099/api/chat/conversations/{conv_id}",
                headers=headers
            )
        print(f"   ✅ 删除 {len(conv_ids)} 个会话")

        print("\n" + "="*40)
        print("✅ 完整流程测试完成")
        print("="*40)


if __name__ == "__main__":
    asyncio.run(test())
