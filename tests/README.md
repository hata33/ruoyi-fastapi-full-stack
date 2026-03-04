# Chat模块API测试说明

## 测试脚本概述

`test_chat_api.py` 是一个完整的API测试脚本，用于测试Chat模块的所有接口。

## 测试覆盖范围

### 1. 认证模块
- `POST /login` - 用户登录
- `GET /getInfo` - 获取用户信息
- `GET /getRouters` - 获取路由菜单
- `POST /logout` - 退出登录

### 2. 模型管理 (`/api/chat/models`)
- `GET /api/chat/models` - 获取模型列表
- `GET /api/chat/models/config` - 获取模型配置
- `POST /api/chat/models/config` - 保存模型配置
- `GET /api/chat/models/presets` - 获取参数预设

### 3. 会话管理 (`/api/chat/conversations`)
- `GET /api/chat/conversations` - 获取会话列表
- `GET /api/chat/conversations/{id}` - 获取会话详情
- `POST /api/chat/conversations` - 创建会话
- `PUT /api/chat/conversations` - 更新会话
- `DELETE /api/chat/conversations/{ids}` - 删除会话
- `PUT /api/chat/conversations/{id}/pin` - 置顶/取消置顶
- `GET /api/chat/conversations/{id}/context` - 获取上下文状态
- `GET /api/chat/conversations/{id}/export` - 导出会话
- `GET /api/chat/conversations/{id}/messages` - 获取会话消息列表

### 4. 消息管理 (`/api/chat/messages`)
- `POST /api/chat/messages/stream` - 发送消息（流式）
- `POST /api/chat/messages/{id}/stop` - 停止生成
- `POST /api/chat/messages/{id}/regenerate` - 重新生成

### 5. 标签管理 (`/api/chat/tags`)
- `GET /api/chat/tags` - 获取标签列表
- `POST /api/chat/tags` - 创建标签
- `DELETE /api/chat/tags/{ids}` - 删除标签

### 6. 用户设置 (`/api/chat/settings`)
- `GET /api/chat/settings` - 获取用户设置
- `PUT /api/chat/settings` - 更新用户设置
- `PUT /api/chat/settings/default-model/{model_id}` - 更新默认模型

### 7. 文件管理 (`/api/chat/files`)
- `POST /api/chat/files/upload` - 上传文件
- `GET /api/chat/files` - 获取文件列表
- `DELETE /api/chat/files/{ids}` - 删除文件

## 使用方法

### 前置条件

1. **启动数据库**
   ```bash
   # 确保PostgreSQL数据库正在运行
   # 默认配置：localhost:5433
   ```

2. **启动API服务器**
   ```bash
   cd D:/Project/AASelf/RuoYi-FastAPI/backend
   python app.py --env dev
   ```

3. **安装依赖**
   ```bash
   pip install httpx
   ```

### 运行测试

```bash
# 使用默认配置运行
cd D:/Project/AASelf/RuoYi-FastAPI/tests
python test_chat_api.py

# 使用环境变量自定义配置
API_BASE_URL=http://localhost:8000 API_USERNAME=admin API_PASSWORD=admin123 python test_chat_api.py
```

### 配置参数

| 参数 | 环境变量 | 默认值 | 说明 |
|------|----------|--------|------|
| base_url | API_BASE_URL | http://localhost:9099/dev-api | API服务器地址 |
| username | API_USERNAME | admin | 登录用户名 |
| password | API_PASSWORD | admin123 | 登录密码 |
| timeout | - | 30 | 请求超时时间(秒) |

## 测试报告

测试完成后会生成以下输出：

1. **控制台输出** - 实时显示测试进度和结果
2. **JSON报告** - 保存为 `test_report_<timestamp>.json`

### 报告格式

```json
{
  "timestamp": "2026-03-04T09:50:00",
  "config": {
    "base_url": "http://localhost:8000",
    "username": "admin"
  },
  "summary": {
    "total": 18,
    "passed": 15,
    "failed": 3,
    "duration": 12.5
  },
  "results": [
    {
      "name": "POST /login",
      "success": true,
      "status_code": 200,
      "response_time": 0.234,
      "error": null
    }
  ]
}
```

## Agent团队工作流程

本项目使用Agent团队进行自动化测试：

1. **test-runner** - 执行测试脚本并收集结果
2. **code-fixer** - 分析失败测试并修复代码问题
3. **team-lead** - 协调团队工作，汇总测试结果

## 常见问题

### 数据库连接失败

```
OSError: Multiple exceptions: [Errno 10061] Connect call failed ('127.0.0.1', 5433)
```

**解决方案**：
1. 检查PostgreSQL服务是否运行
2. 检查配置文件中的数据库端口是否正确
3. 确认数据库用户名密码是否正确

### 认证失败

```
HTTP 401: Unauthorized
```

**解决方案**：
1. 检查用户名密码是否正确
2. 确认用户账号是否被禁用
3. 检查验证码设置

### 流式消息超时

```
Timeout while reading from server
```

**解决方案**：
1. 增加timeout配置
2. 检查DeepSeek API配置
3. 确认网络连接正常

## 扩展测试

### 添加新的测试用例

在 `ChatAPITester` 类中添加新的测试方法：

```python
async def test_new_endpoint(self) -> TestResult:
    """测试新接口"""
    print("\n测试新接口...")

    result = await self._request("GET", "/api/new/endpoint")

    if result.success:
        print(f"  成功")

    return result
```

然后在 `run_all_tests` 方法中添加到测试列表：

```python
tests = [
    # ... 现有测试
    self.test_new_endpoint,
]
```

## 参考资料

- FastAPI官方文档: https://fastapi.tiangolo.com/
- httpx文档: https://www.python-httpx.org/
- DeepSeek API文档: https://platform.deepseek.com/api-docs/
