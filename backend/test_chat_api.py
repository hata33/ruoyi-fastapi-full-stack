import httpx
import asyncio

async def main():
    # 登录获取 token
    async with httpx.AsyncClient() as client:
        login_response = await client.post(
            "http://localhost:9099/login",
            data={"username": "admin", "password": "admin123", "code": "1234"}
        )
        login_data = login_response.json()
        token = login_data.get("token")
        print(f"Token: {token[:50]}...")

        headers = {"Authorization": f"Bearer {token}"}

        # 测试获取模型列表
        print("\n=== 测试获取模型列表 ===")
        models_response = await client.get(
            "http://localhost:9099/api/chat/models",
            headers=headers
        )
        print(f"Status: {models_response.status_code}")
        print(f"Response: {models_response.json()}")

if __name__ == "__main__":
    asyncio.run(main())
