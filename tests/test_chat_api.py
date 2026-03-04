"""
Chat模块API全流程测试脚本

测试覆盖范围：
1. 登录认证
2. 用户信息和路由
3. 模型管理
4. 会话管理
5. 消息管理（流式）
6. 标签管理
7. 用户设置
8. 文件管理
"""

import asyncio
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import httpx
from urllib.parse import urljoin


@dataclass
class TestConfig:
    """测试配置"""
    base_url: str = "http://localhost:9099"
    username: str = "admin"
    password: str = "admin123"
    timeout: int = 30
    verify_ssl: bool = False


@dataclass
class TestResult:
    """测试结果"""
    name: str
    success: bool
    status_code: Optional[int] = None
    response_time: float = 0.0
    error: Optional[str] = None
    data: Optional[Dict] = None


@dataclass
class TestReport:
    """测试报告"""
    total: int = 0
    passed: int = 0
    failed: int = 0
    results: List[TestResult] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0

    def add_result(self, result: TestResult):
        self.results.append(result)
        self.total += 1
        if result.success:
            self.passed += 1
        else:
            self.failed += 1

    def print_report(self):
        duration = self.end_time - self.start_time
        print("\n" + "=" * 80)
        print("API测试报告")
        print("=" * 80)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总耗时: {duration:.2f}秒")
        print(f"总测试数: {self.total}")
        print(f"通过: {self.passed}")
        print(f"失败: {self.failed}")
        print(f"成功率: {(self.passed/self.total*100):.1f}%" if self.total > 0 else "成功率: N/A")
        print("=" * 80)

        if self.failed > 0:
            print("\n失败的测试:")
            for result in self.results:
                if not result.success:
                    print(f"  - {result.name}: {result.error}")

        print("\n详细结果:")
        for result in self.results:
            status = "✓" if result.success else "✗"
            print(f"  {status} {result.name} ({result.response_time*1000:.0f}ms)")
            if result.status_code:
                print(f"      状态码: {result.status_code}")

        print("=" * 80)


class ChatAPITester:
    """Chat API测试类"""

    def __init__(self, config: TestConfig):
        self.config = config
        self.token: Optional[str] = None
        self.client: Optional[httpx.AsyncClient] = None
        self.report = TestReport()
        self.test_data: Dict[str, Any] = {}

    async def __aenter__(self):
        verify = self.config.verify_ssl if self.config.base_url.startswith('https') else False
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            verify=verify
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    def _url(self, path: str) -> str:
        """构建完整URL"""
        return urljoin(self.config.base_url, path)

    def _headers(self, content_type: str = "application/json") -> Dict[str, str]:
        """构建请求头"""
        headers = {
            "Content-Type": content_type,
            "Accept": "application/json"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs
    ) -> TestResult:
        """发送HTTP请求"""
        start_time = time.time()
        name = f"{method} {path}"

        try:
            req_headers = self._headers()
            if headers:
                req_headers.update(headers)

            content = None
            form_data = None
            if data:
                if req_headers.get("Content-Type") == "application/json":
                    content = json.dumps(data)
                elif req_headers.get("Content-Type") == "application/x-www-form-urlencoded":
                    # 移除Content-Type，让httpx自动设置
                    req_headers.pop("Content-Type", None)
                    form_data = data

            response = await self.client.request(
                method=method,
                url=path,
                params=params,
                content=content,
                data=form_data,
                headers=req_headers,
                **kwargs
            )

            response_time = time.time() - start_time

            try:
                response_data = response.json()
            except:
                response_data = {"raw": response.text}

            success = 200 <= response.status_code < 300
            result = TestResult(
                name=name,
                success=success,
                status_code=response.status_code,
                response_time=response_time,
                data=response_data
            )

            if not success:
                result.error = f"HTTP {response.status_code}: {response_data.get('msg', response.text)}"

            return result

        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                name=name,
                success=False,
                response_time=response_time,
                error=str(e)
            )

    async def test_login(self) -> TestResult:
        """测试登录"""
        print("\n[1/18] 测试登录...")

        data = {
            "username": self.config.username,
            "password": self.config.password,
            "code": "",
            "uuid": ""
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        result = await self._request("POST", "/login", data=data, headers=headers)

        if result.success and result.data:
            # 支持两种返回格式
            if result.data.get("code") == 200:
                self.token = result.data.get("data", {}).get("token")
            elif result.data.get("access_token"):
                self.token = result.data.get("access_token")

            if self.token:
                print(f"  登录成功，获取token: {self.token[:20]}...")
            else:
                result.success = False
                result.error = "未能获取token"

        return result

    async def test_get_info(self) -> TestResult:
        """测试获取用户信息"""
        print("\n[2/18] 测试获取用户信息...")
        result = await self._request("GET", "/getInfo")

        if result.success and result.data:
            if result.data.get("code") == 200:
                user_info = result.data.get("data", {})
                self.test_data["user_id"] = user_info.get("user", {}).get("userId")
                print(f"  用户: {user_info.get('user', {}).get('userName')}")

        return result

    async def test_get_routers(self) -> TestResult:
        """测试获取路由"""
        print("\n[3/18] 测试获取路由...")
        result = await self._request("GET", "/getRouters")

        if result.success and result.data:
            if result.data.get("code") == 200:
                routers = result.data.get("data", [])
                print(f"  获取到 {len(routers)} 个路由")

        return result

    async def test_get_models(self) -> TestResult:
        """测试获取模型列表"""
        print("\n[4/18] 测试获取模型列表...")
        result = await self._request("GET", "/api/chat/models")

        if result.success and result.data:
            if result.data.get("code") == 200:
                models = result.data.get("data", [])
                print(f"  获取到 {len(models)} 个模型")
                if models:
                    self.test_data["model_id"] = models[0].get("modelCode")

        return result

    async def test_get_model_config(self) -> TestResult:
        """测试获取模型配置"""
        print("\n[5/18] 测试获取模型配置...")
        result = await self._request("GET", "/api/chat/models/config")

        if result.success and result.data:
            if result.data.get("code") == 200:
                print(f"  模型配置: {result.data.get('data')}")

        return result

    async def test_create_conversation(self) -> TestResult:
        """测试创建会话"""
        print("\n[6/18] 测试创建会话...")

        model_id = self.test_data.get("model_id", "deepseek-chat")
        data = {
            "modelId": model_id,
            "title": "API测试会话"
        }

        result = await self._request("POST", "/api/chat/conversations", data=data)

        if result.success and result.data:
            if result.data.get("code") == 200:
                conversation = result.data.get("data", {})
                self.test_data["conversation_id"] = conversation.get("conversationId")
                print(f"  创建会话成功，ID: {self.test_data['conversation_id']}")

        return result

    async def test_get_conversations(self) -> TestResult:
        """测试获取会话列表"""
        print("\n[7/18] 测试获取会话列表...")
        result = await self._request("GET", "/api/chat/conversations")

        if result.success and result.data:
            if result.data.get("code") == 200:
                rows = result.data.get("rows", [])
                total = result.data.get("total", 0)
                print(f"  获取到 {len(rows)} 个会话，总计 {total}")

        return result

    async def test_get_conversation_detail(self) -> TestResult:
        """测试获取会话详情"""
        print("\n[8/18] 测试获取会话详情...")

        conv_id = self.test_data.get("conversation_id")
        if not conv_id:
            return TestResult(name="GET /api/chat/conversations/{id}", success=False, error="缺少conversation_id")

        result = await self._request("GET", f"/api/chat/conversations/{conv_id}")

        if result.success and result.data:
            if result.data.get("code") == 200:
                print(f"  会话详情: {result.data.get('data', {}).get('title')}")

        return result

    async def test_send_message_stream(self) -> TestResult:
        """测试发送消息（流式）"""
        print("\n[9/18] 测试发送消息（流式）...")

        conv_id = self.test_data.get("conversation_id")
        model_id = self.test_data.get("model_id", "deepseek-chat")

        if not conv_id:
            return TestResult(name="POST /api/chat/messages/stream", success=False, error="缺少conversation_id")

        data = {
            "conversationId": conv_id,
            "content": "你好，请用一句话介绍你自己",
            "modelId": model_id
        }

        start_time = time.time()

        try:
            async with self.client.stream(
                "POST",
                f"/api/chat/messages/stream",
                json=data,
                headers=self._headers(),
                timeout=60.0
            ) as response:
                if response.status_code == 200:
                    content = ""
                    event_count = 0

                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            try:
                                event_data = json.loads(line[5:].strip())
                                event_type = event_data.get("type") or "unknown"

                                if event_type == "message_start":
                                    self.test_data["assistant_message_id"] = event_data.get("assistantMessageId")
                                    self.test_data["user_message_id"] = event_data.get("userMessageId")

                                elif event_type == "content_delta":
                                    content += event_data.get("content", "")

                                elif event_type == "message_end":
                                    self.test_data["final_message_id"] = event_data.get("messageId")

                                event_count += 1
                            except:
                                pass

                    response_time = time.time() - start_time

                    result = TestResult(
                        name="POST /api/chat/messages/stream",
                        success=True,
                        status_code=200,
                        response_time=response_time
                    )
                    print(f"  收到 {event_count} 个事件，内容长度: {len(content)}")
                    return result
                else:
                    return TestResult(
                        name="POST /api/chat/messages/stream",
                        success=False,
                        status_code=response.status_code,
                        error=f"HTTP {response.status_code}"
                    )

        except Exception as e:
            return TestResult(
                name="POST /api/chat/messages/stream",
                success=False,
                response_time=time.time() - start_time,
                error=str(e)
            )

    async def test_get_conversation_messages(self) -> TestResult:
        """测试获取会话消息列表"""
        print("\n[10/18] 测试获取会话消息列表...")

        conv_id = self.test_data.get("conversation_id")
        if not conv_id:
            return TestResult(name="GET /api/chat/conversations/{id}/messages", success=False, error="缺少conversation_id")

        result = await self._request("GET", f"/api/chat/conversations/{conv_id}/messages")

        if result.success and result.data:
            if result.data.get("code") == 200:
                messages = result.data.get("data", {}).get("rows", [])
                print(f"  获取到 {len(messages)} 条消息")

        return result

    async def test_pin_conversation(self) -> TestResult:
        """测试置顶会话"""
        print("\n[11/18] 测试置顶会话...")

        conv_id = self.test_data.get("conversation_id")
        if not conv_id:
            return TestResult(name="PUT /api/chat/conversations/{id}/pin", success=False, error="缺少conversation_id")

        data = {"isPinned": True}
        result = await self._request("PUT", f"/api/chat/conversations/{conv_id}/pin", data=data)

        if result.success and result.data:
            if result.data.get("code") == 200:
                print(f"  置顶成功")

        return result

    async def test_update_conversation(self) -> TestResult:
        """测试更新会话"""
        print("\n[12/18] 测试更新会话...")

        conv_id = self.test_data.get("conversation_id")
        if not conv_id:
            return TestResult(name="PUT /api/chat/conversations", success=False, error="缺少conversation_id")

        data = {
            "conversationId": conv_id,
            "title": "更新后的API测试会话"
        }

        result = await self._request("PUT", "/api/chat/conversations", data=data)

        if result.success and result.data:
            if result.data.get("code") == 200:
                print(f"  更新成功")

        return result

    async def test_get_conversation_context(self) -> TestResult:
        """测试获取会话上下文状态"""
        print("\n[13/18] 测试获取会话上下文状态...")

        conv_id = self.test_data.get("conversation_id")
        if not conv_id:
            return TestResult(name="GET /api/chat/conversations/{id}/context", success=False, error="缺少conversation_id")

        result = await self._request("GET", f"/api/chat/conversations/{conv_id}/context")

        if result.success and result.data:
            if result.data.get("code") == 200:
                context = result.data.get("data", {})
                print(f"  Token使用: {context.get('totalTokens', 0)}/{context.get('maxTokens', 0)}")

        return result

    async def test_get_tags(self) -> TestResult:
        """测试获取标签列表"""
        print("\n[14/18] 测试获取标签列表...")
        result = await self._request("GET", "/api/chat/tags")

        if result.success and result.data:
            if result.data.get("code") == 200:
                tags = result.data.get("data", [])
                print(f"  获取到 {len(tags)} 个标签")

        return result

    async def test_create_tag(self) -> TestResult:
        """测试创建标签"""
        print("\n[15/18] 测试创建标签...")

        data = {
            "tagName": "API测试标签",
            "tagColor": "#FF5733"
        }

        result = await self._request("POST", "/api/chat/tags", data=data)

        if result.success and result.data:
            if result.data.get("code") == 200:
                tag = result.data.get("data", {})
                self.test_data["tag_id"] = tag.get("tagId")
                print(f"  创建标签成功，ID: {self.test_data.get('tag_id')}")

        return result

    async def test_delete_tag(self) -> TestResult:
        """测试删除标签"""
        print("\n[16/18] 测试删除标签...")

        tag_id = self.test_data.get("tag_id")
        if not tag_id:
            return TestResult(name="DELETE /api/chat/tags/{ids}", success=False, error="缺少tag_id")

        result = await self._request("DELETE", f"/api/chat/tags/{tag_id}")

        if result.success and result.data:
            if result.data.get("code") == 200:
                print(f"  删除标签成功")

        return result

    async def test_get_settings(self) -> TestResult:
        """测试获取用户设置"""
        print("\n[17/18] 测试获取用户设置...")
        result = await self._request("GET", "/api/chat/settings")

        if result.success and result.data:
            if result.data.get("code") == 200:
                settings = result.data.get("data", {})
                print(f"  默认模型: {settings.get('defaultModel')}")

        return result

    async def test_logout(self) -> TestResult:
        """测试退出登录"""
        print("\n[18/18] 测试退出登录...")
        result = await self._request("POST", "/logout")

        if result.success and result.data:
            if result.data.get("code") == 200:
                print(f"  退出登录成功")
                self.token = None

        return result

    async def run_all_tests(self) -> TestReport:
        """运行所有测试"""
        print("=" * 80)
        print("开始执行 Chat API 全流程测试")
        print("=" * 80)
        print(f"测试环境: {self.config.base_url}")
        print(f"测试用户: {self.config.username}")

        self.report.start_time = time.time()

        # 按顺序执行测试
        tests = [
            self.test_login,
            self.test_get_info,
            self.test_get_routers,
            self.test_get_models,
            self.test_get_model_config,
            self.test_create_conversation,
            self.test_get_conversations,
            self.test_get_conversation_detail,
            self.test_send_message_stream,
            self.test_get_conversation_messages,
            self.test_pin_conversation,
            self.test_update_conversation,
            self.test_get_conversation_context,
            self.test_get_tags,
            self.test_create_tag,
            self.test_delete_tag,
            self.test_get_settings,
            self.test_logout
        ]

        for test_func in tests:
            test_result = await test_func()
            self.report.add_result(test_result)

        self.report.end_time = time.time()

        return self.report


async def main():
    """主函数"""
    # 从环境变量读取配置，如果没有则使用默认值
    config = TestConfig(
        base_url=os.getenv("API_BASE_URL", "http://localhost:9099"),
        username=os.getenv("API_USERNAME", "admin"),
        password=os.getenv("API_PASSWORD", "admin123"),
    )

    async with ChatAPITester(config) as tester:
        report = await tester.run_all_tests()
        report.print_report()

        # 保存测试报告到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"test_report_{timestamp}.json"

        report_data = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "base_url": config.base_url,
                "username": config.username
            },
            "summary": {
                "total": report.total,
                "passed": report.passed,
                "failed": report.failed,
                "duration": report.end_time - report.start_time
            },
            "results": [
                {
                    "name": r.name,
                    "success": r.success,
                    "status_code": r.status_code,
                    "response_time": r.response_time,
                    "error": r.error
                }
                for r in report.results
            ]
        }

        report_path = os.path.join(os.path.dirname(__file__), report_file)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"\n测试报告已保存到: {report_path}")

        return report.failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
