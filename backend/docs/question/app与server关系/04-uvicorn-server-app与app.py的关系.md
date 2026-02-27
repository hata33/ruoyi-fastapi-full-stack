# `uvicorn server:app` 与 app.py 的关系

## 问题

`uvicorn server:app` 相当于执行了 server 中的启动，而不再和 app.py 有关系吗？

## 回答

**完全正确！✓**

```
uvicorn server:app
        ↓
    导入 server.py
        ↓
    找到 app 对象
        ↓
    启动服务
        ↓
    和 app.py 零关系
```

**app.py 只是一个可选的便捷启动脚本，不是必需的。**

你可以删掉 app.py，项目照样能用 `uvicorn server:app` 启动。
