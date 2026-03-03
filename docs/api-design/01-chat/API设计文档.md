# AI 聊天应用接口设计文档

## 1. 模块概述

本模块提供 AI 聊天应用的完整后端接口，支持多模型对话、流式消息输出、会话管理、多模态文件上传等功能。

**业务场景：**
- 用户可以选择不同的 AI 模型进行对话（DeepSeek-chat、DeepSeek-reasoner）
- 支持流式消息输出，实时展示 AI 生成内容
- 用户可以管理历史会话，包括新建、删除、重命名、置顶、标签分组等操作
- 支持文件上传分析，提供多模态交互能力
- 支持模型参数配置和用户偏好设置

## 2. 数据模型设计

### 2.1 会话表 (chat_conversation)

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| conversation_id | int | 是 | 主键ID |
| title | string | 是 | 会话标题（默认首条消息前20字） |
| model_id | string | 是 | 当前使用的模型ID |
| is_pinned | boolean | 否 | 是否置顶 |
| pin_time | datetime | 否 | 置顶时间 |
| tag_list | string | 否 | 标签列表（JSON数组） |
| total_tokens | int | 否 | 会话累计使用的token数 |
| message_count | int | 否 | 消息数量 |
| user_id | int | 是 | 所属用户ID |
| create_by | string | 否 | 创建者 |
| create_time | datetime | 是 | 创建时间 |
| update_by | string | 否 | 更新者 |
| update_time | datetime | 是 | 更新时间 |
| remark | string | 否 | 备注 |

### 2.2 消息表 (chat_message)

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| message_id | int | 是 | 主键ID |
| conversation_id | int | 是 | 所属会话ID |
| role | string | 是 | 角色（user/assistant/system） |
| content | text | 是 | 消息内容 |
| thinking_content | text | 否 | 推理过程内容（reasoner模型） |
| tokens_used | int | 否 | 本次消息使用的token数 |
| attachments | string | 否 | 附件列表（JSON数组） |
| user_id | int | 是 | 所属用户ID |
| create_time | datetime | 是 | 创建时间 |
| update_time | datetime | 是 | 更新时间 |

### 2.3 模型配置表 (chat_model)

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model_id | int | 是 | 主键ID |
| model_code | string | 是 | 模型代码（如 deepseek-chat） |
| model_name | string | 是 | 模型名称 |
| model_type | string | 是 | 模型类型（chat/reasoner） |
| max_tokens | int | 是 | 最大token数 |
| is_enabled | boolean | 是 | 是否启用 |
| sort_order | int | 否 | 排序顺序 |
| create_time | datetime | 是 | 创建时间 |
| update_time | datetime | 是 | 更新时间 |

### 2.4 用户模型配置表 (chat_user_model_config)

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| config_id | int | 是 | 主键ID |
| user_id | int | 是 | 用户ID |
| model_id | string | 是 | 模型ID |
| temperature | decimal | 否 | 温度参数（0-2） |
| top_p | decimal | 否 | 采样参数（0-1） |
| max_tokens | int | 否 | 最大生成token数 |
| preset_name | string | 否 | 预设名称（creative/balanced/precise） |
| create_time | datetime | 是 | 创建时间 |
| update_time | datetime | 是 | 更新时间 |

### 2.5 文件上传记录表 (chat_file)

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file_id | int | 是 | 主键ID |
| file_name | string | 是 | 文件名 |
| file_path | string | 是 | 文件路径 |
| file_type | string | 是 | 文件类型（pdf/docx/xlsx/pptx/image） |
| file_size | int | 是 | 文件大小（字节） |
| conversation_id | int | 否 | 关联会话ID |
| message_id | int | 否 | 关联消息ID |
| user_id | int | 是 | 所属用户ID |
| create_time | datetime | 是 | 上传时间 |

### 2.6 会话标签表 (chat_conversation_tag)

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| tag_id | int | 是 | 主键ID |
| tag_name | string | 是 | 标签名称 |
| tag_color | string | 否 | 标签颜色 |
| user_id | int | 是 | 所属用户ID |
| create_time | datetime | 是 | 创建时间 |
| update_time | datetime | 是 | 更新时间 |

### 2.7 用户设置表 (chat_user_setting)

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| setting_id | int | 是 | 主键ID |
| user_id | int | 是 | 用户ID |
| theme_mode | string | 是 | 主题模式（light/dark/system） |
| default_model | string | 否 | 默认模型 |
| enable_search | boolean | 否 | 是否启用联网搜索 |
| stream_output | boolean | 是 | 是否启用流式输出 |
| create_time | datetime | 是 | 创建时间 |
| update_time | datetime | 是 | 更新时间 |

## 3. 接口列表

### 3.1 模型管理模块

#### 3.1.1 获取可用模型列表

- **接口说明**：获取所有启用的 AI 模型列表
- **请求方式**：GET
- **接口路径**：`/api/chat/models`
- **权限要求**：`chat:model:list`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| isEnabled | boolean | query | 否 | 是否启用 |

**响应参数：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | int | 状态码 |
| msg | string | 响应消息 |
| data | array | 模型列表 |

**data字段说明：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| modelId | int | 模型ID |
| modelCode | string | 模型代码 |
| modelName | string | 模型名称 |
| modelType | string | 模型类型（chat/reasoner） |
| maxTokens | int | 最大token数 |
| isEnabled | boolean | 是否启用 |
| sortOrder | int | 排序顺序 |

**请求示例：**
```
GET /api/chat/models?isEnabled=true
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": [
    {
      "modelId": 1,
      "modelCode": "deepseek-chat",
      "modelName": "DeepSeek Chat",
      "modelType": "chat",
      "maxTokens": 64000,
      "isEnabled": true,
      "sortOrder": 1
    },
    {
      "modelId": 2,
      "modelCode": "deepseek-reasoner",
      "modelName": "DeepSeek Reasoner",
      "modelType": "reasoner",
      "maxTokens": 64000,
      "isEnabled": true,
      "sortOrder": 2
    }
  ]
}
```

#### 3.1.2 获取用户模型配置

- **接口说明**：获取用户的模型参数配置
- **请求方式**：GET
- **接口路径**：`/api/chat/model-config`
- **权限要求**：`chat:model:config`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| modelId | string | query | 否 | 模型ID |

**响应参数：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | int | 状态码 |
| msg | string | 响应消息 |
| data | object | 配置信息 |

**data字段说明：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| modelId | string | 模型ID |
| temperature | decimal | 温度参数 |
| topP | decimal | 采样参数 |
| maxTokens | int | 最大生成token数 |
| presetName | string | 预设名称 |

**请求示例：**
```
GET /api/chat/model-config?modelId=deepseek-chat
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "modelId": "deepseek-chat",
    "temperature": 0.7,
    "topP": 0.9,
    "maxTokens": 4096,
    "presetName": "balanced"
  }
}
```

#### 3.1.3 保存用户模型配置

- **接口说明**：保存或更新用户的模型参数配置
- **请求方式**：POST
- **接口路径**：`/api/chat/model-config`
- **权限要求**：`chat:model:config:save`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| modelId | string | body | 是 | 模型ID |
| temperature | decimal | body | 否 | 温度参数（0-2） |
| topP | decimal | body | 否 | 采样参数（0-1） |
| maxTokens | int | body | 否 | 最大生成token数 |
| presetName | string | body | 否 | 预设名称（creative/balanced/precise） |

**请求示例：**
```json
{
  "modelId": "deepseek-chat",
  "temperature": 0.7,
  "topP": 0.9,
  "maxTokens": 4096,
  "presetName": "balanced"
}
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "保存成功",
  "data": null
}
```

### 3.2 会话管理模块

#### 3.2.1 获取会话列表（分页）

- **接口说明**：获取当前用户的会话列表，支持分页和筛选
- **请求方式**：GET
- **接口路径**：`/api/chat/conversations`
- **权限要求**：`chat:conversation:list`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| title | string | query | 否 | 会话标题（模糊查询） |
| modelId | string | query | 否 | 模型ID |
| isPinned | boolean | query | 否 | 是否置顶 |
| tagId | int | query | 否 | 标签ID |
| beginTime | string | query | 否 | 开始时间（yyyy-MM-dd） |
| endTime | string | query | 否 | 结束时间（yyyy-MM-dd） |
| pageNum | int | query | 否 | 页码，默认1 |
| pageSize | int | query | 否 | 每页数量，默认20 |

**响应参数：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | int | 状态码 |
| msg | string | 响应消息 |
| data | object | 分页数据 |

**data字段说明：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| rows | array | 会话列表 |
| total | int | 总记录数 |

**rows字段说明：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| conversationId | int | 会话ID |
| title | string | 会话标题 |
| modelId | string | 模型ID |
| isPinned | boolean | 是否置顶 |
| pinTime | string | 置顶时间 |
| tagList | array | 标签列表 |
| totalTokens | int | 累计token数 |
| messageCount | int | 消息数量 |
| createTime | string | 创建时间 |
| updateTime | string | 更新时间 |

**请求示例：**
```
GET /api/chat/conversations?isPinned=true&pageNum=1&pageSize=20
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "rows": [
      {
        "conversationId": 1,
        "title": "Python编程问题",
        "modelId": "deepseek-chat",
        "isPinned": true,
        "pinTime": "2026-03-03 10:00:00",
        "tagList": ["工作", "代码"],
        "totalTokens": 3500,
        "messageCount": 12,
        "createTime": "2026-03-01 09:00:00",
        "updateTime": "2026-03-03 15:30:00"
      }
    ],
    "total": 25
  }
}
```

#### 3.2.2 获取会话详情

- **接口说明**：获取会话详细信息，包括所有消息
- **请求方式**：GET
- **接口路径**：`/api/chat/conversations/{conversationId}`
- **权限要求**：`chat:conversation:query`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| conversationId | int | path | 是 | 会话ID |

**响应参数：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | int | 状态码 |
| msg | string | 响应消息 |
| data | object | 会话详情 |

**data字段说明：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| conversationId | int | 会话ID |
| title | string | 会话标题 |
| modelId | string | 模型ID |
| isPinned | boolean | 是否置顶 |
| tagList | array | 标签列表 |
| totalTokens | int | 累计token数 |
| messageCount | int | 消息数量 |
| messages | array | 消息列表 |
| createTime | string | 创建时间 |
| updateTime | string | 更新时间 |

**messages字段说明：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| messageId | int | 消息ID |
| role | string | 角色（user/assistant/system） |
| content | string | 消息内容 |
| thinkingContent | string | 推理过程内容 |
| tokensUsed | int | 使用的token数 |
| attachments | array | 附件列表 |
| createTime | string | 创建时间 |

**请求示例：**
```
GET /api/chat/conversations/1
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "conversationId": 1,
    "title": "Python编程问题",
    "modelId": "deepseek-chat",
    "isPinned": true,
    "tagList": ["工作", "代码"],
    "totalTokens": 3500,
    "messageCount": 12,
    "messages": [
      {
        "messageId": 1,
        "role": "user",
        "content": "如何用Python实现快速排序？",
        "thinkingContent": null,
        "tokensUsed": 50,
        "attachments": [],
        "createTime": "2026-03-03 10:00:00"
      },
      {
        "messageId": 2,
        "role": "assistant",
        "content": "以下是快速排序的Python实现...",
        "thinkingContent": null,
        "tokensUsed": 300,
        "attachments": [],
        "createTime": "2026-03-03 10:00:05"
      }
    ],
    "createTime": "2026-03-01 09:00:00",
    "updateTime": "2026-03-03 15:30:00"
  }
}
```

#### 3.2.3 新建会话

- **接口说明**：创建新的空白会话
- **请求方式**：POST
- **接口路径**：`/api/chat/conversations`
- **权限要求**：`chat:conversation:add`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| modelId | string | body | 否 | 模型ID，默认使用用户默认模型 |
| title | string | body | 否 | 会话标题，默认"新对话" |
| tagList | array | body | 否 | 标签列表 |

**请求示例：**
```json
{
  "modelId": "deepseek-chat",
  "title": "新对话",
  "tagList": []
}
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "创建成功",
  "data": {
    "conversationId": 123,
    "title": "新对话",
    "modelId": "deepseek-chat",
    "createTime": "2026-03-03 16:00:00"
  }
}
```

#### 3.2.4 更新会话信息

- **接口说明**：更新会话标题、模型、标签等信息
- **请求方式**：PUT
- **接口路径**：`/api/chat/conversations`
- **权限要求**：`chat:conversation:edit`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| conversationId | int | body | 是 | 会话ID |
| title | string | body | 否 | 会话标题（最多50字符） |
| modelId | string | body | 否 | 模型ID |
| tagList | array | body | 否 | 标签列表 |

**请求示例：**
```json
{
  "conversationId": 1,
  "title": "Python编程问题讨论",
  "tagList": ["工作", "代码"]
}
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "更新成功",
  "data": null
}
```

#### 3.2.5 删除会话

- **接口说明**：删除会话，支持批量删除
- **请求方式**：DELETE
- **接口路径**：`/api/chat/conversations/{conversationIds}`
- **权限要求**：`chat:conversation:remove`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| conversationIds | string | path | 是 | 会话ID，多个用逗号分隔 |

**请求示例：**
```
DELETE /api/chat/conversations/1,2,3
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "删除成功",
  "data": null
}
```

#### 3.2.6 置顶/取消置顶会话

- **接口说明**：设置会话的置顶状态
- **请求方式**：PUT
- **接口路径**：`/api/chat/conversations/{conversationId}/pin`
- **权限要求**：`chat:conversation:edit`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| conversationId | int | path | 是 | 会话ID |
| isPinned | boolean | body | 是 | 是否置顶 |

**请求示例：**
```json
{
  "isPinned": true
}
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "操作成功",
  "data": null
}
```

#### 3.2.7 导出会话

- **接口说明**：导出会话内容为指定格式
- **请求方式**：GET
- **接口路径**：`/api/chat/conversations/{conversationId}/export`
- **权限要求**：`chat:conversation:export`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| conversationId | int | path | 是 | 会话ID |
| format | string | query | 是 | 导出格式（markdown/pdf/txt） |

**响应参数：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | int | 状态码 |
| msg | string | 响应消息 |
| data | object | 导出结果 |

**data字段说明：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| downloadUrl | string | 下载链接 |
| fileName | string | 文件名 |
| fileSize | int | 文件大小 |

**请求示例：**
```
GET /api/chat/conversations/1/export?format=markdown
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "导出成功",
  "data": {
    "downloadUrl": "https://example.com/downloads/conversation_1_20260303.md",
    "fileName": "Python编程问题讨论_20260303.md",
    "fileSize": 15360
  }
}
```

#### 3.2.8 获取会话标签列表

- **接口说明**：获取当前用户的所有会话标签
- **请求方式**：GET
- **接口路径**：`/api/chat/tags`
- **权限要求**：`chat:tag:list`

**响应参数：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | int | 状态码 |
| msg | string | 响应消息 |
| data | array | 标签列表 |

**data字段说明：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| tagId | int | 标签ID |
| tagName | string | 标签名称 |
| tagColor | string | 标签颜色 |
| conversationCount | int | 关联会话数 |

**请求示例：**
```
GET /api/chat/tags
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": [
    {
      "tagId": 1,
      "tagName": "工作",
      "tagColor": "#1890ff",
      "conversationCount": 5
    },
    {
      "tagId": 2,
      "tagName": "学习",
      "tagColor": "#52c41a",
      "conversationCount": 3
    }
  ]
}
```

#### 3.2.9 创建会话标签

- **接口说明**：创建新的会话标签
- **请求方式**：POST
- **接口路径**：`/api/chat/tags`
- **权限要求**：`chat:tag:add`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| tagName | string | body | 是 | 标签名称（最多20字符） |
| tagColor | string | body | 否 | 标签颜色（十六进制） |

**请求示例：**
```json
{
  "tagName": "代码",
  "tagColor": "#722ed1"
}
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "创建成功",
  "data": {
    "tagId": 3,
    "tagName": "代码",
    "tagColor": "#722ed1"
  }
}
```

#### 3.2.10 删除会话标签

- **接口说明**：删除会话标签
- **请求方式**：DELETE
- **接口路径**：`/api/chat/tags/{tagIds}`
- **权限要求**：`chat:tag:remove`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| tagIds | string | path | 是 | 标签ID，多个用逗号分隔 |

**请求示例：**
```
DELETE /api/chat/tags/1,2,3
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "删除成功",
  "data": null
}
```

### 3.3 聊天交互模块

#### 3.3.1 发送消息（流式）

- **接口说明**：发送消息并获取AI流式回复（SSE）
- **请求方式**：POST
- **接口路径**：`/api/chat/messages/stream`
- **权限要求**：`chat:message:send`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| conversationId | int | body | 是 | 会话ID |
| content | string | body | 是 | 消息内容 |
| modelId | string | body | 否 | 模型ID（不传则使用会话默认模型） |
| enableSearch | boolean | body | 否 | 是否启用联网搜索，默认false |
| attachments | array | body | 否 | 附件ID列表 |
| temperature | decimal | body | 否 | 温度参数（覆盖默认配置） |
| maxTokens | int | body | 否 | 最大生成token数（覆盖默认配置） |

**attachments字段说明：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| fileId | int | 文件ID |

**请求示例：**
```json
{
  "conversationId": 1,
  "content": "如何用Python实现快速排序？",
  "modelId": "deepseek-chat",
  "enableSearch": false,
  "attachments": []
}
```

**响应说明：**

返回 Server-Sent Events (SSE) 流，每个事件包含：

| 事件类型 | 说明 |
|---------|------|
| message_start | 开始生成消息 |
| content_delta | 内容增量 |
| thinking_start | 开始推理过程（reasoner模型） |
| thinking_delta | 推理内容增量 |
| thinking_end | 结束推理过程 |
| message_end | 结束生成消息 |
| error | 错误信息 |

**SSE事件示例：**
```
event: message_start
data: {"messageId":123}

event: content_delta
data: {"content":"以下是"}

event: content_delta
data: {"content":"快速排序"}

event: message_end
data: {"tokensUsed":300,"totalTokens":3500}
```

#### 3.3.2 停止生成

- **接口说明**：停止当前正在生成的消息
- **请求方式**：POST
- **接口路径**：`/api/chat/messages/{messageId}/stop`
- **权限要求**：`chat:message:stop`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| messageId | int | path | 是 | 消息ID |

**请求示例：**
```
POST /api/chat/messages/123/stop
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "已停止生成",
  "data": null
}
```

#### 3.3.3 重新生成消息

- **接口说明**：对当前用户消息重新生成AI回复
- **请求方式**：POST
- **接口路径**：`/api/chat/messages/{messageId}/regenerate`
- **权限要求**：`chat:message:regenerate`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| messageId | int | path | 是 | 要重新生成的用户消息ID |
| modelId | string | body | 否 | 新的模型ID |

**请求示例：**
```json
{
  "modelId": "deepseek-reasoner"
}
```

**响应说明：**

返回 SSE 流（与发送消息相同）

#### 3.3.4 获取消息列表

- **接口说明**：获取会话的消息列表（支持分页）
- **请求方式**：GET
- **接口路径**：`/api/chat/conversations/{conversationId}/messages`
- **权限要求**：`chat:message:list`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| conversationId | int | path | 是 | 会话ID |
| beforeMessageId | int | query | 否 | 获取此消息之前的消息（向上滚动） |
| pageSize | int | query | 否 | 每页数量，默认50 |

**响应示例：**
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "rows": [
      {
        "messageId": 1,
        "role": "user",
        "content": "如何用Python实现快速排序？",
        "thinkingContent": null,
        "tokensUsed": 50,
        "attachments": [],
        "createTime": "2026-03-03 10:00:00"
      }
    ],
    "total": 12,
    "hasMore": false
  }
}
```

#### 3.3.5 获取会话上下文状态

- **接口说明**：获取当前会话的token使用情况
- **请求方式**：GET
- **接口路径**：`/api/chat/conversations/{conversationId}/context`
- **权限要求**：`chat:conversation:context`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| conversationId | int | path | 是 | 会话ID |

**响应参数：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | int | 状态码 |
| msg | string | 响应消息 |
| data | object | 上下文状态 |

**data字段说明：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| totalTokens | int | 累计使用token数 |
| maxTokens | int | 最大token数 |
| usagePercent | int | 使用百分比 |
| messageCount | int | 消息数量 |
| warningLevel | string | 警告级别（normal/warning/critical） |

**请求示例：**
```
GET /api/chat/conversations/1/context
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "totalTokens": 12000,
    "maxTokens": 64000,
    "usagePercent": 19,
    "messageCount": 25,
    "warningLevel": "normal"
  }
}
```

### 3.4 文件上传模块

#### 3.4.1 上传文件

- **接口说明**：上传文件用于AI分析
- **请求方式**：POST
- **接口路径**：`/api/chat/files/upload`
- **权限要求**：`chat:file:upload`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| file | file | form-data | 是 | 文件 |
| conversationId | int | form-data | 否 | 关联会话ID |

**文件类型支持：**
- PDF：.pdf
- Word：.doc, .docx
- Excel：.xls, .xlsx
- PowerPoint：.ppt, .pptx
- 图片：.jpg, .jpeg, .png, .gif, .webp
- 纯文本：.txt

**响应参数：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | int | 状态码 |
| msg | string | 响应消息 |
| data | object | 文件信息 |

**data字段说明：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| fileId | int | 文件ID |
| fileName | string | 文件名 |
| fileType | string | 文件类型 |
| fileSize | int | 文件大小（字节） |
| filePath | string | 文件路径 |

**请求示例：**
```
POST /api/chat/files/upload
Content-Type: multipart/form-data

file: [binary data]
conversationId: 1
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "上传成功",
  "data": {
    "fileId": 123,
    "fileName": "document.pdf",
    "fileType": "pdf",
    "fileSize": 1024000,
    "filePath": "/uploads/chat/files/2026/03/03/xxx.pdf"
  }
}
```

#### 3.4.2 获取文件列表

- **接口说明**：获取用户上传的文件列表
- **请求方式**：GET
- **接口路径**：`/api/chat/files`
- **权限要求**：`chat:file:list`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| fileType | string | query | 否 | 文件类型筛选 |
| conversationId | int | query | 否 | 会话ID筛选 |
| pageNum | int | query | 否 | 页码，默认1 |
| pageSize | int | query | 否 | 每页数量，默认20 |

**响应示例：**
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "rows": [
      {
        "fileId": 123,
        "fileName": "document.pdf",
        "fileType": "pdf",
        "fileSize": 1024000,
        "conversationId": 1,
        "createTime": "2026-03-03 10:00:00"
      }
    ],
    "total": 5
  }
}
```

#### 3.4.3 删除文件

- **接口说明**：删除上传的文件
- **请求方式**：DELETE
- **接口路径**：`/api/chat/files/{fileIds}`
- **权限要求**：`chat:file:remove`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| fileIds | string | path | 是 | 文件ID，多个用逗号分隔 |

**请求示例：**
```
DELETE /api/chat/files/123,124,125
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "删除成功",
  "data": null
}
```

### 3.5 用户设置模块

#### 3.5.1 获取用户设置

- **接口说明**：获取当前用户的设置信息
- **请求方式**：GET
- **接口路径**：`/api/chat/settings`
- **权限要求**：`chat:setting:query`

**响应参数：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | int | 状态码 |
| msg | string | 响应消息 |
| data | object | 设置信息 |

**data字段说明：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| themeMode | string | 主题模式（light/dark/system） |
| defaultModel | string | 默认模型 |
| enableSearch | boolean | 是否启用联网搜索 |
| streamOutput | boolean | 是否启用流式输出 |
| fontSize | int | 字体大小 |
| language | string | 语言设置 |

**请求示例：**
```
GET /api/chat/settings
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "themeMode": "dark",
    "defaultModel": "deepseek-chat",
    "enableSearch": false,
    "streamOutput": true,
    "fontSize": 14,
    "language": "zh-CN"
  }
}
```

#### 3.5.2 更新用户设置

- **接口说明**：更新用户设置信息
- **请求方式**：PUT
- **接口路径**：`/api/chat/settings`
- **权限要求**：`chat:setting:edit`

**请求参数：**

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| themeMode | string | body | 否 | 主题模式（light/dark/system） |
| defaultModel | string | body | 否 | 默认模型 |
| enableSearch | boolean | body | 否 | 是否启用联网搜索 |
| streamOutput | boolean | body | 否 | 是否启用流式输出 |
| fontSize | int | body | 否 | 字体大小（12-20） |
| language | string | body | 否 | 语言设置 |

**请求示例：**
```json
{
  "themeMode": "dark",
  "defaultModel": "deepseek-chat",
  "enableSearch": false,
  "streamOutput": true,
  "fontSize": 14
}
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "更新成功",
  "data": null
}
```

#### 3.5.3 获取模型参数预设

- **接口说明**：获取系统提供的模型参数预设模板
- **请求方式**：GET
- **接口路径**：`/api/chat/model-presets`
- **权限要求**：`chat:model:presets`

**响应参数：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | int | 状态码 |
| msg | string | 响应消息 |
| data | array | 预设列表 |

**data字段说明：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| presetName | string | 预设名称（creative/balanced/precise） |
| displayName | string | 显示名称 |
| description | string | 描述 |
| temperature | decimal | 温度参数 |
| topP | decimal | 采样参数 |

**请求示例：**
```
GET /api/chat/model-presets
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": [
    {
      "presetName": "creative",
      "displayName": "创意型",
      "description": "更高的随机性，适合创意写作",
      "temperature": 1.2,
      "topP": 0.95
    },
    {
      "presetName": "balanced",
      "displayName": "平衡型",
      "description": "平衡的输出，适合日常对话",
      "temperature": 0.7,
      "topP": 0.9
    },
    {
      "presetName": "precise",
      "displayName": "精确型",
      "description": "更确定的输出，适合代码生成",
      "temperature": 0.3,
      "topP": 0.8
    }
  ]
}
```

## 4. 业务逻辑说明

### 4.1 会话创建与标题生成

- 新建会话时，标题默认为"新对话"
- 发送首条消息后，自动将标题更新为首条消息的前20个字符
- 用户可手动修改标题，修改后不再自动更新

### 4.2 流式消息处理

- 使用 SSE (Server-Sent Events) 实现流式输出
- 消息生成过程中，前端可随时停止生成
- 停止后已生成内容保留，可重新生成或继续对话
- reasoner 模型会先输出思考过程（thinking_content），再输出最终回复

### 4.3 上下文窗口管理

- 每个会话记录累计使用的 token 数
- 当接近模型最大 token 数时，返回警告状态
- 前端根据警告级别显示不同颜色提示
- 建议用户在达到 80% 时考虑新建会话

### 4.4 会话置顶规则

- 置顶会话按置顶时间倒序排列
- 非置顶会话按更新时间倒序排列
- 置顶会话始终显示在列表顶部

### 4.5 文件上传限制

- 单个文件最大 10MB
- 支持的文件类型：PDF、Word、Excel、PowerPoint、图片、纯文本
- 上传的文件与用户关联，用户只能看到自己上传的文件
- 文件保留 30 天后自动清理

### 4.6 数据隔离

- 所有查询默认只返回当前登录用户的数据
- 用户只能操作自己的会话、消息、文件和标签
- 接口自动从 JWT token 中获取用户 ID

## 5. 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 操作成功 |
| 401 | 未授权，请先登录 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 413 | 文件大小超过限制 |
| 415 | 不支持的文件类型 |
| 429 | 请求过于频繁，请稍后再试 |
| 500 | 服务器错误 |
| 1001 | 会话不存在 |
| 1002 | 消息不存在 |
| 1003 | 模型不可用 |
| 1004 | 文件上传失败 |
| 1005 | 会话标题不能为空 |
| 1006 | 会话标题超过50字符 |
| 1007 | 消息内容不能为空 |
| 1008 | 标签名称已存在 |
| 1009 | 模型调用失败 |
| 1010 | 聊天服务暂时不可用 |

## 6. 前端开发注意事项

### 6.1 接口调用

1. **Token 传递**：所有接口需要在请求头中携带 token
   ```
   Authorization: Bearer {token}
   ```

2. **时间格式**：所有时间字段返回格式为 `yyyy-MM-dd HH:mm:ss`

3. **分页处理**：
   - 列表接口统一使用 `pageNum` 和 `pageSize` 参数
   - 响应中 `total` 表示总记录数

4. **错误处理**：
   - 统一判断 `code === 200` 表示成功
   - 其他情况使用 `msg` 显示错误信息

### 6.2 SSE 流式处理

1. **连接建立**：使用 `EventSource` 或 `fetch` + `ReadableStream`

2. **事件处理**：
   ```javascript
   const eventSource = new EventSource('/api/chat/messages/stream');
   eventSource.addEventListener('message_start', (e) => {
       // 开始生成
   });
   eventSource.addEventListener('content_delta', (e) => {
       const data = JSON.parse(e.data);
       // 追加内容
   });
   ```

3. **连接关闭**：停止生成或消息结束后关闭连接

### 6.3 文件上传

1. 使用 `FormData` 上传文件
2. 上传前验证文件类型和大小
3. 上传成功后保存 fileId，发送消息时关联

### 6.4 状态管理

1. 会话列表需要实时更新（新建、删除、更新）
2. 消息列表支持追加和滚动加载
3. 输入框状态使用 localStorage 持久化

### 6.5 用户体验优化

1. 发送消息后立即显示用户消息，AI 消息显示加载占位
2. 流式输出时显示"停止"按钮
3. 接近 token 上限时显示警告提示
4. 错误发生时显示友好的错误提示

## 7. 后续扩展接口规划

以下接口为 v2.0 规划，暂不实现：

| 接口 | 描述 | 优先级 |
|------|------|--------|
| `GET /api/chat/conversations/search` | 会话搜索（标题和内容） | P3 |
| `POST /api/chat/messages/{messageId}/branch` | 创建消息分支 | P2 |
| `POST /api/chat/conversations/{conversationId}/share` | 生成会话分享链接 | P2 |
| `GET /api/chat/statistics` | 获取用户使用统计 | P2 |

---

**文档结束**
