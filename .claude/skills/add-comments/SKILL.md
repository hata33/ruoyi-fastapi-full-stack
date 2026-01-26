---
name: add-comments
description: 为代码添加详细的初学者友好注释
---

# 为代码添加详细注释

为代码文件添加易于理解的中文注释，帮助初学者学习。

## 执行步骤

1. 读取用户指定的文件或当前文件
2. 分析代码结构和功能
3. 使用 Edit 工具添加注释，包括：
   - 文件顶部的模块说明
   - 类和函数的文档字符串
   - 复杂逻辑的行内注释
   - 逻辑区块的分隔注释

## 注释原则

- 使用清晰的中文，适合初学者理解
- 解释"做什么"和"为什么"，不只重复代码
- 保留已有的好注释
- 不注释显而易见的简单代码
- 遵循项目现有的注释风格

## 不同语言的注释格式

**Python**: 使用 `"""` 文档字符串 + `#` 行内注释
**JavaScript/TypeScript**: 使用 JSDoc 格式 `/** */`
**Vue**: 使用 `<!-- -->` 组件注释
**SQL**: 使用 `--` 注释

## 示例

**修改前:**
```python
def authenticate(username, password):
    user = db.query(User).filter_by(username=username).first()
    if user and verify_password(password, user.password_hash):
        return create_token(user.id)
    return None
```

**修改后:**
```python
def authenticate(username: str, password: str) -> Optional[str]:
    """
    用户认证函数

    验证用户名和密码，成功则返回JWT令牌。

    参数:
        username: 用户名
        password: 明文密码

    返回:
        JWT令牌字符串，失败返回None
    """
    # 从数据库查找用户
    user = db.query(User).filter_by(username=username).first()

    # 验证密码，bcrypt自动处理盐值比较
    if user and verify_password(password, user.password_hash):
        return create_token(user.id)

    # 认证失败
    return None
```
