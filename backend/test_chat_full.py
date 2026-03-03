import httpx
import asyncio
import json

async def main():
    # 登录获取 token
    async with httpx.AsyncClient() as client:
        login_response = await client.post(
            "http://localhost:9099/login",
            data={"username": "admin", "password": "admin123", "code": "1234"}
        )
        login_data = login_response.json()
        token = login_data.get("token")
        headers = {"Authorization": f"Bearer {token}"}

        # 1. 测试获取模型列表
        print("=== 1. 测试获取模型列表 ===")
        models_response = await client.get(
            "http://localhost:9099/api/chat/models",
            headers=headers
        )
        models = models_response.json().get("data", [])
        for model in models:
            print(f"  - {model['modelName']} ({model['modelCode']})")

        # 2. 测试创建会话
        print("\n=== 2. 测试创建会话 ===")
        create_conversation = await client.post(
            "http://localhost:9099/api/chat/conversations",
            headers=headers,
            json={
                "title": "测试会话",
                "modelId": "deepseek-chat"
            }
        )
        print(f"Status: {create_conversation.status_code}")
        conversation_data = create_conversation.json()
        print(f"Response: {conversation_data}")

        conversation_id = conversation_data.get("data", {}).get("conversationId")
        print(f"会话ID: {conversation_id}")

        if conversation_id:
            # 3. 测试发送消息（流式）
            print(f"\n=== 3. 测试发送消息（会话ID: {conversation_id}） ===")

            async with client.stream(
                "POST",
                "http://localhost:9099/api/chat/messages/stream",
                headers=headers,
                json={
                    "conversationId": conversation_id,
                    "content": "你好，请介绍一下你自己",
                    "modelId": "deepseek-chat"
                }
            ) as response:
                print(f"Status: {response.status_code}")
                print("SSE 响应:")
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        try:
                            event_data = json.loads(data)
                            event = event_data.get("event", "")
                            if event:
                                print(f"  Event: {event}")
                            if event in ["content_delta", "thinking_delta"]:
                                content = event_data.get("data", {}).get("content", "")
                                print(f"    Content: {content[:50]}...")
                            elif event == "message_end":
                                tokens = event_data.get("data", {}).get("tokensUsed", 0)
                                print(f"    Tokens: {tokens}")
                        except:
                            pass
                    elif line.strip():
                        print(f"  {line}")

if __name__ == "__main__":
    asyncio.run(main())
