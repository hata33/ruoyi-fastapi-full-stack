# AI聊天应用模块

## 模块概述

本模块提供 AI 聊天应用的完整后端接口，支持多模型对话、流式消息输出、会话管理、多模态文件上传等功能。

## 技术栈

- **框架**: FastAPI
- **ORM**: SQLAlchemy (异步)
- **数据验证**: Pydantic v2
- **数据库**: MySQL / PostgreSQL

## 模块结构

```
module_chat/
├── __init__.py              # 模块初始化
├── application.py           # 应用配置，路由注册
├── controller/              # 控制器层
│   ├── __init__.py
│   ├── chat_model_controller.py       # 模型管理
│   ├── chat_conversation_controller.py # 会话管理
│   ├── chat_message_controller.py     # 消息管理
│   ├── chat_file_controller.py        # 文件上传
│   └── chat_setting_controller.py     # 用户设置
├── service/                 # 服务层
│   ├── __init__.py
│   ├── chat_model_service.py
│   ├── chat_conversation_service.py
│   ├── chat_message_service.py
│   ├── chat_file_service.py
│   └── chat_setting_service.py
├── dao/                     # 数据访问层
│   ├── __init__.py
│   ├── chat_model_dao.py
│   ├── chat_conversation_dao.py
│   ├── chat_message_dao.py
│   ├── chat_file_dao.py
│   └── chat_setting_dao.py
├── entity/                  # 实体层
│   ├── __init__.py
│   ├── do/                  # 数据库对象
│   │   ├── __init__.py
│   │   ├── chat_conversation_do.py
│   │   ├── chat_message_do.py
│   │   ├── chat_model_do.py
│   │   ├── chat_user_model_config_do.py
│   │   ├── chat_file_do.py
│   │   ├── chat_conversation_tag_do.py
│   │   └── chat_user_setting_do.py
│   └── vo/                  # 视图对象
│       ├── __init__.py
│       ├── common_vo.py
│       ├── chat_model_vo.py
│       ├── chat_conversation_vo.py
│       ├── chat_message_vo.py
│       ├── chat_file_vo.py
│       └── chat_setting_vo.py
├── sql/                     # 数据库脚本
│   └── init_chat_tables.sql  # 初始化表结构
└── README.md                # 模块说明
```

## 数据表设计

### 1. chat_conversation（聊天会话表）
存储用户的聊天会话信息，包括标题、模型、置顶状态、标签等。

### 2. chat_message（聊天消息表）
存储会话中的消息内容，包括用户消息、AI回复、推理过程等。

### 3. chat_model（聊天模型配置表）
存储支持的 AI 模型配置信息。

### 4. chat_user_model_config（用户模型配置表）
存储用户自定义的模型参数配置。

### 5. chat_file（聊天文件上传记录表）
存储用户上传的文件信息。

### 6. chat_conversation_tag（会话标签表）
存储用户自定义的会话标签。

### 7. chat_user_setting（用户设置表）
存储用户的个人偏好设置。

## API 接口

### 模型管理模块
- `GET /api/chat/models` - 获取可用模型列表
- `GET /api/chat/models/config` - 获取用户模型配置
- `POST /api/chat/models/config` - 保存用户模型配置
- `GET /api/chat/models/presets` - 获取模型参数预设

### 会话管理模块
- `GET /api/chat/conversations` - 获取会话列表（分页）
- `GET /api/chat/conversations/{conversation_id}` - 获取会话详情
- `POST /api/chat/conversations` - 新建会话
- `PUT /api/chat/conversations` - 更新会话信息
- `DELETE /api/chat/conversations/{conversation_ids}` - 删除会话
- `PUT /api/chat/conversations/{conversation_id}/pin` - 置顶/取消置顶会话
- `GET /api/chat/conversations/{conversation_id}/context` - 获取会话上下文状态
- `GET /api/chat/conversations/{conversation_id}/export` - 导出会话

### 标签管理模块
- `GET /api/chat/tags` - 获取会话标签列表
- `POST /api/chat/tags` - 创建会话标签
- `DELETE /api/chat/tags/{tag_ids}` - 删除会话标签

### 消息管理模块
- `POST /api/chat/messages/stream` - 发送消息（流式）
- `POST /api/chat/messages/{message_id}/stop` - 停止生成
- `POST /api/chat/messages/{message_id}/regenerate` - 重新生成消息
- `GET /api/chat/messages/conversations/{conversation_id}` - 获取消息列表

### 文件上传模块
- `POST /api/chat/files/upload` - 上传文件
- `GET /api/chat/files` - 获取文件列表
- `DELETE /api/chat/files/{file_ids}` - 删除文件

### 用户设置模块
- `GET /api/chat/settings` - 获取用户设置
- `PUT /api/chat/settings` - 更新用户设置
- `PUT /api/chat/settings/default-model/{model_id}` - 更新默认模型

## 使用说明

### 1. 数据库初始化

执行 SQL 脚本创建数据表：

```bash
mysql -u root -p < backend/module_chat/sql/init_chat_tables.sql
```

### 2. 注册模块

在主应用中注册聊天模块：

```python
# 在 app.py 或 server.py 中
from module_chat.application import ChatModuleConfig

# 注册聊天模块
ChatModuleConfig(app)
```

### 3. 配置权限

确保在系统菜单中配置相应的权限标识：

- `chat:model:list` - 模型列表查询
- `chat:conversation:list` - 会话列表查询
- `chat:conversation:add` - 会话新增
- `chat:conversation:edit` - 会话编辑
- `chat:conversation:remove` - 会话删除
- `chat:message:send` - 消息发送
- `chat:file:upload` - 文件上传
- ... (其他权限)

## 注意事项

1. **流式输出**: 消息发送接口使用 SSE (Server-Sent Events) 实现流式输出
2. **文件上传**: 支持的文件类型包括 PDF、Word、Excel、PPT、图片、文本
3. **Token 管理**: 会话会自动累计 token 使用量，接近上限时会返回警告
4. **数据隔离**: 所有查询默认只返回当前登录用户的数据

## 待实现功能

- [ ] AI 服务集成（DeepSeek API 调用）
- [ ] 联网搜索功能
- [ ] 会话分享功能
- [ ] 消息分支功能
- [ ] 使用统计功能
