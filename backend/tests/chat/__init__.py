"""
聊天模块测试套件

测试目录结构：
tests/chat/
├── __init__.py              # 本文件（测试索引）
├── test_deepseek_client.py  # TEST-001: DeepSeek 客户端单元测试
├── test_deepseek_simple.py  # TEST-002: DeepSeek 流式简化测试
├── test_deepseek_stream.py  # TEST-003: 完整端到端测试
└── TEST_SOP.md              # 测试标准操作程序
└── TEST_RESULT.md           # 测试结果报告

运行方式：
1. 运行单个测试：
   python tests/chat/test_deepseek_client.py
   python tests/chat/test_deepseek_simple.py
   python tests/chat/test_deepseek_stream.py

2. 运行所有测试（需要安装 pytest）：
   pytest tests/chat/ -v

测试覆盖：
- DeepSeek 客户端功能
- 流式数据输出
- Reasoner 推理模型
- 端到端 API 测试
"""

__version__ = "1.0.0"
__author__ = "RuoYi Team"
