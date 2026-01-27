# FastAPI 核心知识点学习指南

本目录基于 RuoYi-Vue3-FastAPI 项目代码，系统地讲解 FastAPI 框架的核心知识点。

## 学习路径

建议按照以下顺序学习，每个知识点都结合了项目中的实际代码示例：

### 基础篇

1. **[FastAPI 简介与项目结构](./01-FastAPI简介与项目结构.md)**
   - FastAPI 框架概述
   - 项目目录结构
   - 应用启动流程

2. **[路由与请求方法](./02-路由与请求方法.md)**
   - 路由定义与装饰器
   - HTTP 请求方法
   - 路径参数与查询参数
   - 路由分组与模块化

3. **[请求参数与验证](./03-请求参数与验证.md)**
   - 路径参数
   - 查询参数
   - 请求头参数
   - Cookie 参数
   - 表单数据
   - Pydantic 验证器

4. **[请求体与 Pydantic 模型](./04-请求体与Pydantic模型.md)**
   - Pydantic BaseModel
   - 嵌套模型
   - 验证规则
   - 自定义验证器

### 进阶篇

5. **[响应模型与序列化](./05-响应模型与序列化.md)**
   - 响应模型定义
   - 序列化配置
   - 数据脱敏
   - 统一响应格式

6. **[依赖注入系统](./06-依赖注入系统.md)**
   - Depends 依赖
   - 类作为依赖
   - 依赖嵌套
   - 全局依赖
   - 上下文管理

7. **[中间件](./07-中间件.md)**
   - 中间件原理
   - 自定义中间件
   - CORS 中间件
   - 日志中间件
   - 执行顺序

8. **[异常处理](./08-异常处理.md)**
   - 异常处理器
   - 自定义异常
   - 全局异常处理
   - HTTPException

### 高级篇

9. **[异步编程](./09-异步编程.md)**
   - async/await 语法
   - 异步数据库操作
   - 异步任务
   - 并发控制

10. **[安全性与认证](./10-安全性与认证.md)**
    - JWT 认证
    - OAuth2
    - 密码加密
    - 权限验证

11. **[数据库集成](./11-数据库集成.md)**
    - SQLAlchemy 配置
    - ORM 模型定义
    - CRUD 操作
    - 事务管理
    - 连接池

12. **[Redis 缓存](./12-Redis缓存.md)**
    - Redis 连接配置
    - 缓存操作
    - 缓存策略
    - 分布式锁

### 实战篇

13. **[文件上传处理](./13-文件上传处理.md)**
    - 文件上传接口
    - 文件类型验证
    - 文件存储
    - 大文件处理

14. **[配置管理](./14-配置管理.md)**
    - 环境变量
    - 配置文件
    - Pydantic Settings
    - 多环境配置

15. **[生命周期事件](./15-生命周期事件.md)**
    - 启动事件
    - 关闭事件
    - 资源初始化
    - 优雅关闭

## 学习建议

### 如何使用本教程

1. **代码对照学习**：每个知识点都配有项目中的实际代码示例，建议在 IDE 中打开对应文件对照学习
2. **实践练习**：每个知识点都有练习建议，建议动手实践
3. **循序渐进**：按照目录顺序学习，不要跳跃
4. **查阅文档**：遇到问题时，参考 [FastAPI 官方文档](https://fastapi.tiangolo.com/)

### 项目代码位置

本教程引用的代码主要位于：
- `ruoyi-fastapi-backend/server.py` - 应用入口
- `ruoyi-fastapi-backend/module_admin/` - 业务模块
- `ruoyi-fastapi-backend/core/` - 核心功能
- `ruoyi-fastapi-backend/config/` - 配置文件
- `ruoyi-fastapi-backend/common/` - 公共组件

### 前置知识

在学习本教程前，建议掌握：
- Python 3.8+ 基础语法
- 异步编程基础（async/await）
- HTTP 协议基础
- 数据库基础概念

### 版本说明

本教程基于以下技术版本：
- **FastAPI**: 0.100.0+
- **Pydantic**: 2.0+
- **SQLAlchemy**: 2.0+
- **Python**: 3.8+

注意：不同版本的 API 可能有差异，请根据实际版本查阅官方文档。

## 学习资源

### 官方资源
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [FastAPI GitHub](https://github.com/tiangolo/fastapi)
- [Pydantic 文档](https://docs.pydantic.dev/)

### 推荐阅读
- [FastAPI 教程](https://fastapi.tiangolo.com/tutorial/)
- [Python 异步编程](https://docs.python.org/3/library/asyncio.html)

## 反馈与贡献

如果您在学习过程中发现问题或有改进建议，欢迎：
- 提交 Issue
- 发起 Pull Request
- 参与讨论

---

**开始学习**：从 [01-FastAPI简介与项目结构](./01-FastAPI简介与项目结构.md) 开始您的 FastAPI 学习之旅！
