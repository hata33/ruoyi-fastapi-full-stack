"""
会话管理测试
测试会话的 CRUD 操作
"""
import httpx
import asyncio
import json


async def test():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 登录
        print("=== 登录 ===")
        login = await client.post(
            "http://localhost:9099/login",
            data={"username": "admin", "password": "admin123", "code": "1234"}
        )
        token = login.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. 获取会话列表
        print("\n=== 1. 获取会话列表 ===")
        list_resp = await client.get(
            "http://localhost:9099/api/chat/conversations",
            headers=headers,
            params={"page_num": 1, "page_size": 10}
        )
        print(f"状态码: {list_resp.status_code}")
        result = list_resp.json()

        if result.get("code") == 200:
            rows = result.get("rows", [])
            print(f"[PASS] 获取列表成功，共 {len(rows)} 条")
            if rows:
                conv_id = rows[0].get("conversationId")
                print(f"   第一条会话ID: {conv_id}")

                # 2. 获取会话详情
                print("\n=== 2. 获取会话详情 ===")
                detail_resp = await client.get(
                    f"http://localhost:9099/api/chat/conversations/{conv_id}",
                    headers=headers
                )
                print(f"状态码: {detail_resp.status_code}")
                print(f"响应: {json.dumps(detail_resp.json(), ensure_ascii=False)[:200]}")

                # 3. 更新会话
                print("\n=== 3. 更新会话 ===")
                update_resp = await client.put(
                    "http://localhost:9099/api/chat/conversations",
                    headers=headers,
                    json={
                        "conversationId": conv_id,
                        "title": "更新后的标题",
                        "modelId": "deepseek-chat"
                    }
                )
                print(f"状态码: {update_resp.status_code}")
                print(f"响应: {update_resp.json()}")

                # 检查 tag_list 解析
                print("\n=== 检查 tag_list 解析 ===")
                list_resp2 = await client.get(
                    "http://localhost:9099/api/chat/conversations",
                    headers=headers,
                    params={"page_num": 1, "page_size": 1}
                )
                rows2 = list_resp2.json().get("rows", [])
                if rows2:
                    tag_list = rows2[0].get("tag_list")
                    if isinstance(tag_list, list):
                        print(f"[PASS] tag_list 正确解析为数组: {tag_list}")
                    else:
                        print(f"[FAIL] tag_list 类型错误: {type(tag_list)}, 值: {tag_list}")
        else:
            print(f"[FAIL] 获取列表失败: {result.get('msg')}")


if __name__ == "__main__":
    asyncio.run(test())
