"""
简化版 Chat 接口测试
"""
import httpx
import asyncio
import json

# 登录并测试
async def test():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 登录
        print("=== 1. 登录 ===")
        login = await client.post(
            "http://localhost:9099/login",
            data={"username": "admin", "password": "admin123", "code": "1234"}
        )
        token = login.json()["token"]
        print(f"Token: {token[:50]}...")

        headers = {"Authorization": f"Bearer {token}"}

        # 2. 创建会话
        print("\n=== 2. 创建会话 ===")
        conv = await client.post(
            "http://localhost:9099/api/chat/conversations",
            headers=headers,
            json={
                "title": "测试会话",
                "modelId": "deepseek-chat"
            }
        )
        print(f"Status: {conv.status_code}")
        print(f"Response: {conv.text[:500]}")

if __name__ == "__main__":
    asyncio.run(test())
