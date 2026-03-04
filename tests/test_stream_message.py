"""
Chat模块流式消息接口测试

重点测试: POST /api/chat/messages/stream
"""

import asyncio
import json
import httpx
import time


class StreamMessageTester:
    def __init__(self, base_url="http://localhost:9099"):
        self.base_url = base_url
        self.token = None
        self.client = None

    async def login(self, username="admin", password="admin123"):
        """登录获取token"""
        print("=== 1. 登录 ===")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/login",
                data={
                    "username": username,
                    "password": password,
                    "code": "",
                    "uuid": ""
                }
            )
            result = response.json()
            print(f"登录响应: {json.dumps(result, ensure_ascii=False)}")

            if result.get("code") == 200:
                self.token = result.get("data", {}).get("token")
                if self.token:
                    print(f"[OK] Login success, Token: {self.token[:30]}...")
                    return True

            # 尝试从swagger格式获取
            if result.get("access_token"):
                self.token = result.get("access_token")
                print(f"[OK] Login success (Swagger), Token: {self.token[:30]}...")
                return True

            # 尝试直接从响应获取token
            if result.get("token"):
                self.token = result.get("token")
                print(f"[OK] Login success (Direct), Token: {self.token[:30]}...")
                return True

            print("[FAIL] Login failed")
            return False

    async def get_models(self):
        """获取可用模型列表"""
        print("\n=== 2. 获取模型列表 ===")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/chat/models",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            result = response.json()
            print(f"模型列表: {json.dumps(result, ensure_ascii=False, indent=2)}")

            if result.get("code") == 200:
                models = result.get("data", [])
                if models:
                    model_code = models[0].get("modelCode", "deepseek-chat")
                    print(f"[OK] Using model: {model_code}")
                    return model_code

            return "deepseek-chat"

    async def create_conversation(self, model_id="deepseek-chat"):
        """创建会话"""
        print("\n=== 3. 创建会话 ===")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/chat/conversations",
                json={
                    "modelId": model_id,
                    "title": "流式消息测试"
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )
            result = response.json()
            print(f"创建会话响应: {json.dumps(result, ensure_ascii=False)}")

            if result.get("code") == 200:
                conv_id = result.get("data", {}).get("conversationId")
                if conv_id:
                    print(f"[OK] Conversation created, ID: {conv_id}")
                    return conv_id

            print("[FAIL] Conversation creation failed")
            return None

    async def send_stream_message(self, conversation_id, model_id="deepseek-chat"):
        """发送流式消息"""
        print("\n=== 4. 发送流式消息 ===")
        print(f"会话ID: {conversation_id}")
        print(f"模型: {model_id}")
        print("消息内容: 你好，请用一句话介绍你自己")
        print("\n--- 流式响应开始 ---")

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat/messages/stream",
                json={
                    "conversationId": conversation_id,
                    "content": "你好，请用一句话介绍你自己",
                    "modelId": model_id
                },
                headers={"Authorization": f"Bearer {self.token}"}
            ) as response:
                if response.status_code != 200:
                    print(f"[FAIL] Request failed: {response.status_code}")
                    text = await response.aread()
                    print(f"Error: {text.decode()}")
                    return False

                content = ""
                thinking_content = ""
                event_count = 0
                start_time = time.time()
                debug_lines = []

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    # 解析SSE格式
                    if line.startswith("event:"):
                        event_type = line.split(":", 1)[1].strip()
                        continue

                    if line.startswith("data:"):
                        try:
                            data_str = line[5:].strip()
                            data = json.loads(data_str)
                            event_count += 1

                            # 调试：记录前10行原始数据
                            if len(debug_lines) < 10:
                                debug_lines.append(line)

                            # 根据数据内容判断事件类型
                            if "userMessageId" in data and "assistantMessageId" in data:
                                # message_start 事件
                                user_msg_id = data.get("userMessageId")
                                asst_msg_id = data.get("assistantMessageId")
                                print(f"[Event] Message start - User ID: {user_msg_id}, Assistant ID: {asst_msg_id}")

                            elif "messageId" in data and "content" in data and "tokensUsed" in data:
                                # message_end 事件
                                final_id = data.get("messageId")
                                tokens_used = data.get("tokensUsed", 0)
                                total_tokens = data.get("totalTokens", 0)
                                print(f"\n[Event] Message end - ID: {final_id}, Tokens: {tokens_used}/{total_tokens}")

                            elif "content" in data and len(data) == 1:
                                # content_delta 事件
                                delta = data.get("content", "")
                                content += delta
                                # 安全打印，避免emoji编码问题
                                try:
                                    print(delta, end="", flush=True)
                                except UnicodeEncodeError:
                                    # 如果包含无法编码的字符，显示占位符
                                    print("?", end="", flush=True)

                            elif "error" in data:
                                # 错误事件
                                error_msg = data.get("message", "Unknown error")
                                print(f"\n[Error] {error_msg}")
                                return False

                        except json.JSONDecodeError:
                            pass

                duration = time.time() - start_time
                print(f"\n--- Stream Response End ---")
                print(f"Events received: {event_count}")
                print(f"Response time: {duration:.2f}s")
                print(f"Content length: {len(content)} chars")
                print(f"Thinking length: {len(thinking_content)} chars")

                # 调试输出
                if debug_lines:
                    print(f"\n[DEBUG] First {len(debug_lines)} lines:")
                    for i, dl in enumerate(debug_lines):
                        print(f"  {i+1}: {dl[:200]}")

                if content:
                    print(f"\n[OK] Stream message success")
                    return True
                else:
                    print(f"[FAIL] No content received")
                    return False

    async def run_full_test(self):
        """运行完整测试流程"""
        print("=" * 60)
        print("Chat模块流式消息接口测试")
        print("=" * 60)

        # 1. 登录
        if not await self.login():
            print("\n[FAIL] Cannot login")
            return False

        # 2. 获取模型
        model_id = await self.get_models()

        # 3. 创建会话
        conv_id = await self.create_conversation(model_id)
        if not conv_id:
            print("\n[FAIL] Cannot create conversation")
            return False

        # 4. 发送流式消息
        success = await self.send_stream_message(conv_id, model_id)

        print("\n" + "=" * 60)
        if success:
            print("Test Result: [OK] PASS")
        else:
            print("Test Result: [FAIL] FAIL")
        print("=" * 60)

        return success


async def main():
    tester = StreamMessageTester()
    success = await tester.run_full_test()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
