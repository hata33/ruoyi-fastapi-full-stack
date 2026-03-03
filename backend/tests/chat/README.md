# 聊天模块接口测试

## 目录结构

```
tests/chat/
├── README.md                   # 本文件
├── TEST_SOP.md                 # 测试 SOP 文档
├── INTERFACE_COMPARISON.md     # 接口对比分析（当前实现 vs 文档）
├── __init__.py                 # 测试套件初始化
├── run_all_tests.py            # 一键运行所有测试
├── 01_test_basic_api.py        # 基础 API 测试
├── 02_test_conversation.py     # 会话管理测试
├── 03_test_pin_and_tags.py     # 置顶和标签测试
├── 04_test_full_flow.py        # 完整流程测试
├── 05_test_new_features.py     # 新增功能测试
├── 06_test_deepseek_client.py  # DeepSeek 客户端测试
├── 07_test_deepseek_simple.py  # 流式数据简化测试
└── 08_test_deepseek_stream.py  # 端到端流式测试
```

## 文档说明

| 文档 | 说明 |
|------|------|
| **TEST_SOP.md** | 测试标准操作程序，包含环境准备、启动流程、测试步骤 |
| **INTERFACE_COMPARISON.md** | 接口对比分析，对比当前实现与 PRD/API设计文档的符合度 |

## DeepSeek 测试套件

### 快速测试

```bash
# 运行所有 DeepSeek 测试
pytest tests/chat/06_test_deepseek*.py tests/chat/07_test_deepseek*.py tests/chat/08_test_deepseek*.py -v

# 单独运行测试
python tests/chat/06_test_deepseek_client.py  # 客户端单元测试
python tests/chat/07_test_deepseek_simple.py  # 简化集成测试
python tests/chat/08_test_deepseek_stream.py  # 完整端到端测试
```

### 测试说明

#### 06_test_deepseek_client.py - DeepSeek 客户端测试
- **类型**: 单元测试
- **内容**: DeepSeek Client 功能验证
- **测试项**:
  - ✓ 模拟模式（无 API Key）
  - ✓ Reasoner 推理模型
  - ○ 真实 API（需配置 Key）

#### 07_test_deepseek_simple.py - 流式数据简化测试
- **类型**: 集成测试
- **内容**: 流式输出验证
- **测试项**:
  - ✓ Chat 模型流式输出
  - ✓ Reasoner 推理流程

#### 08_test_deepseek_stream.py - 端到端流式测试
- **类型**: 端到端测试
- **内容**: 完整 API 流程
- **测试项**:
  - ✓ 用户认证
  - ✓ 创建会话
  - ✓ 流式消息
  - ✓ SSE 事件格式

## 原有测试套件

## 快速开始

### 1. 启动服务器
```bash
cd D:\Project\AASelf\RuoYi-FastAPI\backend
python start_server.py
```

### 2. 运行测试

#### 方式一：一键运行所有测试
```bash
python tests/chat/run_all_tests.py
```

#### 方式二：单独运行某个测试
```bash
# 基础测试
python tests/chat/01_test_basic_api.py

# 会话管理测试
python tests/chat/02_test_conversation.py

# 置顶和标签测试
python tests/chat/03_test_pin_and_tags.py

# 完整流程测试
python tests/chat/04_test_full_flow.py
```

## 测试说明

### 01_test_basic_api.py
- 测试登录功能
- 测试创建会话
- 验证 model_id 字段正确保存

### 02_test_conversation.py
- 测试获取会话列表（分页）
- 测试获取会话详情
- 测试更新会话
- 验证 tag_list 字段正确解析为 JSON 数组

### 03_test_pin_and_tags.py
- 测试置顶会话
- 测试验证置顶效果
- 测试取消置顶
- 测试创建/获取/删除标签

### 04_test_full_flow.py
- 模拟完整用户使用场景
- 创建多个会话
- 置顶重要会话
- 创建分类标签
- 清理测试数据

## 测试前检查清单

- [ ] 服务器已启动 (http://localhost:9099)
- [ ] 管理员账号可用 (username: admin, password: admin123)
- [ ] DeepSeek API Key 已配置
- [ ] 数据库表已创建

## 常见问题

### Q: 提示 "服务器未启动"
**A:** 先运行 `python start_server.py` 启动服务器

### Q: 登录失败
**A:** 检查验证码是否固定为 "1234"，账号密码是否正确

### Q: 创建标签提示 "标签名称已存在"
**A:** 测试脚本已自动使用随机后缀避免冲突

### Q: model_id 为 NULL
**A:** 检查 Pydantic 模型是否设置了正确的 alias 配置

## 退出测试

按 `Ctrl+C` 停止测试脚本，服务器继续运行。

如需停止服务器，另开终端运行：
```bash
taskkill /F /IM python.exe
```
