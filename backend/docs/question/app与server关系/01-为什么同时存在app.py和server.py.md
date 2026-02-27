# 为什么同时存在 app.py 和 server.py？

## 问题

为什么 backend 目录下同时有 `app.py` 和 `server.py` 两个文件？

## 回答

**职责分离：**

| 文件 | 作用 |
|------|------|
| `server.py` | **核心文件** - 创建 FastAPI 应用实例 `app`，配置路由、中间件、生命周期 |
| `app.py` | **启动入口** - 用于 `python app.py` 直接运行 |

**启动命令 `server:app` 含义：**
- `server` → 模块名（server.py）
- `app` → 该模块中定义的实例名

这是 uvicorn 的标准格式：`模块名:实例名`
