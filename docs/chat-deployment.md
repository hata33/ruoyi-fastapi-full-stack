# Chat 模块部署说明

## 已完成的集成工作

### 1. DeepSeek API 集成 ✅

**创建的文件：**
- `backend/module_chat/service/deepseek_client.py` - DeepSeek API 客户端

**功能特性：**
- 支持 `deepseek-chat` 和 `deepseek-reasoner` 模型
- SSE 流式响应处理
- 推理过程（reasoner 模型）处理
- 自动降级到模拟模式（未配置 API Key 时）
- 错误处理和重试机制

**使用方式：**
```python
from module_chat.service.deepseek_client import get_deepseek_client

client = get_deepseek_client()
async for event in client.chat_stream(messages, model="deepseek-chat"):
    # 处理流式响应
    pass
```

### 2. 环境变量配置 ✅

**更新的文件：**
- `backend/config/env.py` - 添加 `DeepSeekSettings` 配置类
- `backend/.env.dev` - 添加 DeepSeek 配置项

**新增配置项：**
```bash
# DeepSeek API Key（请替换为你的真实 API Key）
DEEPSEEK_API_KEY = 'your-deepseek-api-key-here'
# API 地址（默认官方地址）
DEEPSEEK_API_BASE = 'https://api.deepseek.com/v1'
# 请求超时（秒）
DEEPSEEK_TIMEOUT = 60
# 最大重试次数
DEEPSEEK_MAX_RETRIES = 3
```

### 3. 路由注册 ✅

**更新的文件：**
- `backend/server.py` - 注册 chat 模块的所有控制器

**新增路由：**
- `/api/chat/models` - 模型管理
- `/api/chat/conversations` - 会话管理
- `/api/chat/tags` - 标签管理
- `/api/chat/messages` - 消息管理
- `/api/chat/files` - 文件管理
- `/api/chat/settings` - 用户设置

### 4. 控制器更新 ✅

**更新的文件：**
- `backend/module_chat/controller/chat_message_controller.py`
- `backend/module_chat/service/chat_message_service.py`
- `backend/module_chat/dao/chat_message_dao.py`

**新增方法：**
- `ChatMessageService.build_conversation_messages()` - 构建对话历史
- `ChatMessageDao.get_recent_messages()` - 获取最近消息

---

## 部署步骤

### 步骤 1：配置 DeepSeek API Key

编辑 `backend/.env.dev` 文件：

```bash
# 替换为你的真实 API Key
DEEPSEEK_API_KEY = 'sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
```

> 💡 如何获取 DeepSeek API Key：
> 1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com/)
> 2. 注册/登录账号
> 3. 进入 API Keys 页面
> 4. 创建新的 API Key

### 步骤 2：创建数据库表

SQLAlchemy 支持自动创建表。如果你使用 PostgreSQL，确保 `config/get_db.py` 中配置了 `create_all`。

**手动创建表（可选）：**
```bash
psql -U postgres -d hata-service-platform -f backend/module_chat/sql/init_chat_tables.sql
```

### 步骤 3：安装依赖

```bash
cd backend
pip install httpx
```

### 步骤 4：启动应用

```bash
cd backend
python server.py
```

或使用 uvicorn：
```bash
uvicorn server:app --host 0.0.0.0 --port 9099 --reload
```

### 步骤 5：验证部署

访问 API 文档：
```
http://localhost:9099/docs
```

查看"聊天"分组下的所有接口。

---

## 测试 API

### 发送消息测试

```bash
curl -X POST "http://localhost:9099/api/chat/messages/stream" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversationId": 1,
    "content": "你好，请介绍一下你自己",
    "modelId": "deepseek-chat"
  }'
```

### 获取可用模型

```bash
curl -X GET "http://localhost:9099/api/chat/models" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 配置说明

### 模型参数

可以在发送消息时传递模型参数：

| 参数 | 类型 | 范围 | 说明 |
|------|------|------|------|
| `temperature` | float | 0.0-2.0 | 温度参数，越高越随机 |
| `top_p` | float | 0.0-1.0 | 采样参数 |
| `max_tokens` | int | 1-64000 | 最大生成 token 数 |

### 推理过程

使用 `deepseek-reasoner` 模型时，响应会包含推理过程：

```javascript
// SSE 事件流
event: thinking_start
data: {}

event: thinking_delta
data: {"content": "思考内容..."}

event: thinking_end
data: {}

event: content_delta
data: {"content": "实际回复内容"}

event: message_end
data: {"tokensUsed": 1234}
```

---

## 故障排查

### 问题 1：API Key 未配置

**症状：**
- 日志显示 "DEEPSEEK_API_KEY 未配置，将使用模拟模式"
- AI 回复是模拟内容

**解决：**
检查 `.env.dev` 文件中是否正确配置了 `DEEPSEEK_API_KEY`。

### 问题 2：API 请求失败

**症状：**
- 错误日志显示 "AI 服务请求失败: 401"
- SSE 流返回 error 事件

**解决：**
1. 检查 API Key 是否正确
2. 检查 API Key 是否有余额
3. 检查网络连接

### 问题 3：数据库表不存在

**症状：**
- 错误日志显示 "relation \"chat_conversation\" does not exist"

**解决：**
```bash
# 手动执行 SQL 初始化脚本
psql -U postgres -d hata-service-platform -f backend/module_chat/sql/init_chat_tables.sql
```

---

## 生产环境配置

编辑 `backend/.env.prod`：

```bash
# 使用生产环境的 API Key
DEEPSEEK_API_KEY = 'sk-prod-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# 可选：使用代理或自定义端点
DEEPSEEK_API_BASE = 'https://your-proxy.com/v1'

# 调整超时时间（生产环境建议更长）
DEEPSEEK_TIMEOUT = 120
```

---

## 下一步优化

1. **缓存优化**：缓存模型配置，减少数据库查询
2. **监控告警**：添加 API 调用成功率、响应时间监控
3. **限流控制**：添加用户级别的调用频率限制
4. **Token 管理**：实现更精确的 token 统计和预警
5. **多模型支持**：扩展支持其他 AI 模型（OpenAI、Claude 等）

---

**部署完成时间：** 2026-03-03
**文档版本：** v1.0
