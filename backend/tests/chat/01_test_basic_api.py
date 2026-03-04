"""
基础 API 测试
测试登录和创建会话功能
"""
import httpx
import asyncio


async def test():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 登录
        print("=== 1. 登录 ===")
        login = await client.post(
            "http://localhost:9099/login",
            data={"username": "admin", "password": "admin@123", "code": "1234"}
        )
        print(f"状态码: {login.status_code}")
        if login.status_code != 200:
            print(f"登录失败: {login.text}")
            return

        token = login.json()["token"]
        print(f"Token: {token[:30]}...")

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
        print(f"状态码: {conv.status_code}")
        result = conv.json()
        print(f"响应: {result}")

        # 验证点
        if result.get("code") == 200:
            data = result.get("data", {})
            conv_id = data.get("conversation_id")
            model_id = data.get("model_id")
            print(f"\n[PASS] 测试通过")
            print(f"   会话ID: {conv_id}")
            print(f"   模型ID: {model_id}")

            if model_id == "deepseek-chat":
                print("   [PASS] model_id 正确保存")
            else:
                print(f"   [FAIL] model_id 错误: 期望 'deepseek-chat', 实际 '{model_id}'")
        else:
            print(f"\n[FAIL] 测试失败: {result.get('msg')}")


if __name__ == "__main__":
    asyncio.run(test())
