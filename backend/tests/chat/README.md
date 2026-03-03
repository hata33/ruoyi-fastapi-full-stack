# 聊天模块接口测试

## 目录结构

```
tests/chat/
├── README.md                  # 本文件
├── TEST_SOP.md                # 测试 SOP 文档
├── run_all_tests.py           # 一键运行所有测试
├── 01_test_basic_api.py       # 基础 API 测试
├── 02_test_conversation.py    # 会话管理测试
├── 03_test_pin_and_tags.py    # 置顶和标签测试
└── 04_test_full_flow.py       # 完整流程测试
```

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
