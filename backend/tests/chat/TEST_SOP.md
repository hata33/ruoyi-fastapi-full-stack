# 聊天模块接口测试 SOP

## 一、环境准备

### 1.1 确认服务器状态
```bash
# 检查是否有 Python 进程占用 9099 端口
netstat -ano | findstr :9099

# 如有占用，终止进程（替换 <PID>）
taskkill /F /PID <PID>
```

### 1.2 确认环境变量
检查 `.env.dev` 文件中 DeepSeek 配置：
```bash
DEEPSEEK_API_KEY = 'sk-xxx'
DEEPSEEK_API_BASE = 'https://api.deepseek.com/v1'
```

### 1.3 确认数据库表
确保以下表已创建：
- `chat_model` - AI 模型表
- `chat_conversation` - 会话表
- `chat_conversation_tag` - 标签表
- `chat_message` - 消息表
- `chat_file` - 文件表
- `chat_user_setting` - 用户设置表

---

## 二、启动服务器

### 2.1 启动命令
```bash
# 进入后端目录
cd D:\Project\AASelf\RuoYi-FastAPI\backend

# 启动服务器
python start_server.py
```

### 2.2 验证启动成功
- 控制台显示：`INFO: Application startup complete`
- 访问 http://localhost:9099/docs 可看到 API 文档

---

## 三、执行测试

### 3.1 测试脚本目录
```
backend/tests/chat/
├── 01_test_basic_api.py      # 基础接口测试（登录、创建会话）
├── 02_test_conversation.py   # 会话管理测试（列表、详情、CRUD）
├── 03_test_pin_and_tags.py   # 置顶和标签测试
└── 04_test_full_flow.py      # 完整流程测试
```

### 3.2 执行顺序

#### Step 1: 基础 API 测试
```bash
python tests/chat/01_test_basic_api.py
```
**验证点：**
- [ ] 登录成功获取 token
- [ ] 创建会话成功
- [ ] model_id 正确保存

#### Step 2: 会话管理测试
```bash
python tests/chat/02_test_conversation.py
```
**验证点：**
- [ ] 获取会话列表（分页）
- [ ] 获取会话详情
- [ ] 更新会话（标题、模型）
- [ ] 删除会话
- [ ] tag_list 正确解析为 JSON 数组

#### Step 3: 置顶和标签测试
```bash
python tests/chat/03_test_pin_and_tags.py
```
**验证点：**
- [ ] 置顶会话成功
- [ ] 置顶后会话排在列表前面
- [ ] 取消置顶成功
- [ ] 创建标签成功
- [ ] 获取标签列表
- [ ] 删除标签成功

#### Step 4: 完整流程测试
```bash
python tests/chat/04_test_full_flow.py
```
**验证点：**
- [ ] 完整业务流程跑通

---

## 四、常见问题检查清单

### 4.1 Pydantic 字段映射问题
**症状：** 数据库字段为 NULL，但前端传了值

**检查点：**
- [ ] VO 模型是否设置了 `alias='fieldId'`
- [ ] VO 模型是否设置了 `populate_by_name=True`
- [ ] Service 层是否使用数据库实体而非 VO 模型

**修复示例：**
```python
# 错误写法
class AddModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)
    model_id: str  # 无法解析 modelId

# 正确写法
class AddModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    model_id: str = Field(alias='modelId')
```

### 4.2 SQLAlchemy 批量更新问题
**症状：** `bulk synchronize of persistent objects not supported`

**检查点：**
- [ ] DAO 层 update 语句是否添加了 `execution_options`

**修复示例：**
```python
# 错误写法
await db.execute(
    update(Table).where(Table.id == id).values(field=value)
)

# 正确写法
await db.execute(
    update(Table)
    .where(Table.id == id)
    .values(field=value)
    .execution_options(synchronize_session=False)
)
```

### 4.3 字段访问方式问题
**症状：** `'dict' object has no attribute 'xxx'`

**检查点：**
- [ ] Service 层是否兼容 dict 和对象两种访问方式

**修复示例：**
```python
# 兼容写法
value = row.get('field') if isinstance(row, dict) else getattr(row, 'field', None)
```

### 4.4 控制器类型注解问题
**症状：** `422 Unprocessable Entity` - `Field required`

**检查点：**
- [ ] Controller 参数是否有类型注解
- [ ] 类型注解是否与 `@ValidateFields(validate_model='xxx')` 匹配

**修复示例：**
```python
# 错误写法
async def add_tag(request: Request, add_tag, ...):  # 缺少类型

# 正确写法
async def add_tag(request: Request, add_tag: AddTagModel, ...):
```

---

## 五、测试报告模板

### 5.1 测试结果记录
```
测试日期：____________
测试人员：____________

| 接口 | 方法 | 状态 | 问题描述 |
|------|------|------|----------|
| 登录 | POST | ✅/❌ | |
| 创建会话 | POST | ✅/❌ | |
| 会话列表 | GET | ✅/❌ | |
| 置顶会话 | PUT | ✅/❌ | |
| 创建标签 | POST | ✅/❌ | |
| 删除标签 | DELETE | ✅/❌ | |

通过率：____/____
```

### 5.2 问题记录
```
问题序号 | 问题描述 | 修复方案 | 验证状态
---------|----------|----------|----------
```

---

## 六、快速命令参考

```bash
# 一键启动服务器
cd D:\Project\AASelf\RuoYi-FastAPI\backend && python start_server.py

# 一键停止所有 Python 进程
taskkill /F /IM python.exe

# 检查端口
netstat -ano | findstr :9099

# 运行所有测试
for %f in (tests\chat\*.py) do python %f
```
