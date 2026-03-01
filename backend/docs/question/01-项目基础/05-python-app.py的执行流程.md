# `python app.py` 的执行流程

## 问题

执行 `python app.py` 相当于执行了 app.py，又在 app.py 中执行了 `uvicorn server:app`？

## 回答

**完全正确！✓**

```
python app.py
      ↓
执行 app.py 代码
      ↓
进入 if __name__ == '__main__'
      ↓
执行 uvicorn.run(app='server:app', ...)
      ↓
相当于在内部调用了 uvicorn server:app
```

**两种方式最终效果一样：**

```bash
# 方式1：手动
uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# 方式2：通过 app.py（自动执行上面那行）
python app.py
```

**app.py 本质上就是 uvicorn 命令的 Python 版本封装。**
