# Web 安全基础

> 安全是后端开发的生命线。了解常见的安全威胁和防护措施，能帮助你构建更安全的应用。

## 目录

- [安全概述](#安全概述)
- [认证与授权](#认证与授权)
- [JWT 认证](#jwt-认证)
- [常见安全威胁](#常见安全威胁)
- [数据加密](#数据加密)
- [输入验证](#输入验证)
- [项目中的安全实践](#项目中的安全实践)

---

## 安全概述

### 为什么重要

```
┌─────────────────────────────────┐
│          不安全的系统             │
│                                 │
│  数据泄露  →  用户信任丧失  →  业务损失  │
│  账号被盗  →  法律风险  →  公司倒闭   │
└─────────────────────────────────┘
```

### 纵深防御

安全不是单一措施，而是多层防护：

```
┌─────────────────────────────────┐
│        网络层：防火墙、HTTPS         │
├─────────────────────────────────┤
│      应用层：认证、授权、输入验证     │
├─────────────────────────────────┤
│      数据层：加密、访问控制、备份     │
├─────────────────────────────────┤
│      监控层：日志、审计、异常检测     │
└─────────────────────────────────┘
```

---

## 认证与授权

### 认证 (Authentication)

**认证**：验证"你是谁"

```
┌──────────┐                    ┌──────────┐
│   用户   │                    │  服务器   │
└────┬─────┘                    └────┬─────┘
     │                               │
     │  1. 提交身份证明（用户名+密码）  │
     │ ──────────────────────────>│
     │                               │
     │  2. 验证身份                   │
     │ <──────────────────────────│
     │  验证成功，返回 Token          │
     │                               │
```

### 授权 (Authorization)

**授权**：验证"你能做什么"

```
┌──────────┐                    ┌──────────┐
│   用户   │  Token             │  服务器   │
│  (Token) │                    │          │
└────┬─────┘                    └────┬─────┘
     │                               │
     │  1. 携带 Token 请求资源         │
     │ ──────────────────────────>│
     │                               │
     │  2. 检查权限                   │
     │ <──────────────────────────│
     │  有权限：返回资源               │
     │  无权限：返回 403               │
     │                               │
```

### 认证 vs 授权

| 对比项 | 认证 (Authentication) | 授权 (Authorization) |
|--------|---------------------|---------------------|
| 问题 | 你是谁？ | 你能做什么？ |
| 时机 | 首次访问时 | 每次请求时 |
| 示例 | 登录 | 检查是否有删除权限 |
| 状态码 | 401 Unauthorized | 403 Forbidden |
| 英文简写 | AuthN | AuthZ |

---

## JWT 认证

### 什么是 JWT

JWT（JSON Web Token）是一种**轻量级的跨域认证解决方案**。

```
JWT 结构：header.payload.signature
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE2MTYyMzkwMjJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
└─────────────┬─────────────┘ └─────────────────────┬─────────────────────┘
              Header                                  Payload
                                                 └────────────────────┬────────────────────┘
                                                      Signature
```

### JWT 的三部分

#### 1. Header（头部）

```json
{
  "alg": "HS256",  // 签名算法
  "typ": "JWT"     // 令牌类型
}

// Base64 编码
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9
```

#### 2. Payload（载荷）

```json
{
  "user_id": "1",
  "user_name": "admin",
  "session_id": "abc123",
  "exp": 1704067200  // 过期时间
}

// Base64 编码
eyJ1c2VyX2lkIjoiMSIsImV4cCI6MTcwNDA2NzIwMH0
```

#### 3. Signature（签名）

```
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  secret
)
```

### JWT 工作流程

```
┌──────────┐                              ┌──────────┐
│   客户端  │                              │  服务器   │
└────┬─────┘                              └────┬─────┘
     │                                         │
     │  1. 登录请求（用户名+密码）                │
     │ ─────────────────────────────────────>│
     │                                         │
     │  2. 验证成功，生成 JWT                   │
     │ <────────────────────────────────────│
     │  eyJ0eXAiOiJKV1QiLCJhbGc...             │
     │                                         │
     │  3. 存储到 localStorage                 │
     │  localStorage.setItem('token', jwt)    │
     │                                         │
     │  4. 后续请求携带 Token                  │
     │ ─────────────────────────────────────>│
     │  Authorization: Bearer eyJ0eXAi...     │
     │                                         │
     │  5. 验证 Token，返回数据                │
     │ <────────────────────────────────────│
     │                                         │
```

### 项目中的 JWT 实现

```python
# module_admin/service/login_service.py
import jwt
from datetime import datetime, timedelta

class JwtConfig:
    jwt_secret_key: str = "your-secret-key"  # 密钥
    jwt_algorithm: str = "HS256"              # 算法
    jwt_expire_minutes: int = 30              # 过期时间

@classmethod
async def create_access_token(cls, data: dict, expires_delta: timedelta = None):
    """生成 JWT Token"""
    to_encode = data.copy()

    # 设置过期时间
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)

    to_encode.update({"exp": expire})

    # 生成 JWT
    encoded_jwt = jwt.encode(
        to_encode,
        JwtConfig.jwt_secret_key,
        algorithm=JwtConfig.jwt_algorithm
    )
    return encoded_jwt

# 使用
token = await LoginService.create_access_token(
    data={
        "user_id": str(user.user_id),
        "user_name": user.user_name,
        "session_id": session_id
    },
    expires_delta=timedelta(minutes=30)
)
```

### Token 验证

```python
@classmethod
async def get_current_user(
    cls,
    request: Request,
    token: str = Depends(oauth2_scheme),
    query_db: AsyncSession = Depends(get_db)
):
    """获取当前登录用户"""

    # 1. 解析 JWT
    try:
        payload = jwt.decode(
            token,
            JwtConfig.jwt_secret_key,
            algorithms=[JwtConfig.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError:
        raise AuthException(data="", message="Token已过期")
    except jwt.JWTError:
        raise AuthException(data="", message="Token验证失败")

    # 2. 提取用户信息
    user_id: str = payload.get("user_id")
    session_id: str = payload.get("session_id")

    # 3. 验证 Redis 中的 Token
    redis_token = await request.app.state.redis.get(
        f"{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}"
    )

    if token != redis_token:
        raise AuthException(data="", message="Token已失效")

    # 4. 返回用户信息
    return current_user
```

### JWT 安全建议

✅ **推荐做法**：

1. 使用 HTTPS 传输
2. 密钥足够复杂且定期更换
3. 设置合理的过期时间
4. 敏感数据不放入 Payload
5. Token 存储在内存（不推荐 localStorage）

❌ **避免**：

1. 在 Payload 中存储密码
2. 永不过期的 Token
3. 使用简单的密钥（如 "secret"）
4. 在 URL 中传递 Token

---

## 常见安全威胁

### 1. SQL 注入

**原理**：攻击者通过输入恶意 SQL，操纵数据库查询。

```python
# ❌ 危险：字符串拼接
def get_user(username):
    sql = f"SELECT * FROM users WHERE username = '{username}'"
    # 攻击输入：username = "admin' OR '1'='1"
    # 实际执行：SELECT * FROM users WHERE username = 'admin' OR '1'='1'
    # 结果：绕过验证，获取所有用户数据

# ✅ 安全：参数化查询
def get_user(username):
    stmt = select(SysUser).where(SysUser.user_name == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
```

### 2. XSS（跨站脚本攻击）

**原理**：攻击者注入恶意脚本，窃取用户数据。

```html
<!-- ❌ 危险：直接渲染用户输入 -->
<div>{{ user_input }}</div>
<!-- 攻击输入：<script>alert('XSS')</script> -->

<!-- ✅ 安全：转义输出 -->
<div>{{ user_input | escape }}</div>
```

**防护**：
- 前端对输出进行转义
- 设置 Content-Security-Policy 响应头
- HttpOnly Cookie（防止 JS 读取）

### 3. CSRF（跨站请求伪造）

**原理**：攻击者诱导用户在已登录状态下执行非预期操作。

```
用户已登录银行网站
↓
访问恶意网站（包含隐藏表单）
↓
表单自动提交到银行网站
↓
银行执行转账操作（因为用户已登录）
```

**防护**：
- CSRF Token
- 验证 Referer 头
- SameSite Cookie 属性

```python
# 项目中的 CSRF 防护
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

# FastAPI 的 OAuth2 流程自带 CSRF 防护
```

### 4. 暴力破解

**原理**：攻击者不断尝试不同的用户名和密码组合。

**防护**：

```python
# 项目中的防护措施

# 1. 验证码
if captcha_enabled:
    await check_captcha(code, uuid)

# 2. 密码错误计数
error_count = await redis.get(f"password_error:{username}")
if error_count > 5:
    raise LoginException(message="密码错误次数过多，账号已锁定")

# 3. 账号锁定
await redis.set(
    f"account_lock:{username}",
    "locked",
    ex=timedelta(minutes=10)
)

# 4. IP 黑名单
if ip in blacklist:
    raise LoginException(message="IP已被封禁")
```

---

## 数据加密

### 哈希算法

哈希是**单向**的，无法从哈希值还原原始数据。用于密码存储。

```python
import bcrypt

# 哈希密码
password = "admin123".encode('utf-8')
hashed = bcrypt.hashpw(password, bcrypt.gensalt())

# 验证密码
if bcrypt.checkpw(password, hashed):
    print("密码正确")
```

### 对称加密

加密和解密使用**相同**的密钥。

```python
from cryptography.fernet import Fernet

# 生成密钥
key = Fernet.generate_key()
cipher = Fernet(key)

# 加密
encrypted = cipher.encrypt(b"sensitive data")

# 解密
decrypted = cipher.decrypt(encrypted)
```

### HTTPS

HTTPS = HTTP + SSL/TLS，保证数据传输安全。

```
┌──────────┐          ┌──────────┐
│   客户端  │          │  服务器   │
└────┬─────┘          └────┬─────┘
     │                     │
     │  1. 请求连接           │
     │ ──────────────────>│
     │                     │
     │  2. 返回证书           │
     │ <──────────────────│
     │                     │
     │  3. 验证证书           │
     │  生成会话密钥          │
     │                     │
     │  4. 加密通信           │
     │ <═════════════════>│
     │  (加密数据)           │
```

---

## 输入验证

### 为什么需要验证

```
用户输入 ──┬── 合法数据 ──> 处理
          │
          └── 恶意数据 ──> ❌ 安全漏洞
```

### 验证策略

```python
# 1. 类型验证
class UserModel(BaseModel):
    user_id: int
    user_name: str
    email: str

# 2. 格式验证
from pydantic import validator

class UserModel(BaseModel):
    email: str

    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('邮箱格式错误')
        return v

# 3. 长度验证
class UserModel(BaseModel):
    user_name: str = Field(min_length=3, max_length=30)

# 4. 业务规则验证
class UserModel(BaseModel):
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码至少8位')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含数字')
        return v
```

### 白名单 vs 黑名单

```
黑名单：过滤已知的危险输入
❌ 不安全：总有漏网之鱼

白名单：只允许已知的合法输入
✅ 安全：默认拒绝，只放行允许的
```

```python
# ❌ 黑名单（不安全）
def sanitize(input):
    dangerous = ["<script>", "alert(", "onerror="]
    for d in dangerous:
        input = input.replace(d, "")
    return input

# ✅ 白名单（安全）
def validate_username(username):
    if not re.match(r'^[a-zA-Z0-9_]{3,30}$', username):
        raise ValueError("用户名格式错误")
    return username
```

---

## 项目中的安全实践

### 密码安全

```python
# utils/pwd_util.py
import bcrypt

class PwdUtil:
    @staticmethod
    def encrypt_password(password: str) -> str:
        """加密密码"""
        pwd_bytes = password.encode('utf-8')
        hashed = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt())
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
```

### 权限控制

```python
# module_admin/aspect/interface_auth.py
class CheckUserInterfaceAuth:
    """接口权限校验"""

    def __init__(self, perms: str):
        self.perms = perms

    async def __call__(self, current_user: CurrentUserService = Depends()):
        # 超级管理员拥有所有权限
        if 1 in [role.role_id for role in current_user.roles]:
            return True

        # 检查用户权限列表
        if self.perms not in current_user.permissions:
            raise PermissionException(data="", message="权限不足")

        return True

# 使用
@userController.post("/add")
async def add_user(
    user: UserModel,
    _: bool = Depends(CheckUserInterfaceAuth("system:user:add"))
):
    # 只有拥有 system:user:add 权限的用户才能执行
    pass
```

### 数据权限

```python
# module_admin/aspect/data_scope.py
class GetDataScope:
    """数据权限范围控制"""

    async def __call__(self, current_user: CurrentUserService = Depends()):
        # 全部数据权限
        if '1' in [role.data_scope for role in current_user.roles]:
            return "1 == 1"

        # 自定义数据权限
        # 本部门数据权限
        # 本部门及以下数据权限
        # 仅本人数据权限

        # 返回 SQL 条件
        return "dept_id IN (1, 2, 3)"
```

### 敏感信息脱敏

```python
def mask_email(email: str) -> str:
    """邮箱脱敏"""
    if '@' not in email:
        return email
    username, domain = email.split('@')
    if len(username) <= 2:
        return f"{'*' * len(username)}@{domain}"
    return f"{username[0]}{'*' * (len(username) - 2)}{username[-1]}@{domain}"

def mask_phone(phone: str) -> str:
    """手机号脱敏"""
    if len(phone) < 7:
        return phone
    return f"{phone[:3]}****{phone[-4:]}"
```

### 安全响应头

```python
# middlewares/security_headers.py
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # 防止点击劫持
    response.headers["X-Frame-Options"] = "DENY"

    # 防止 MIME 类型嗅探
    response.headers["X-Content-Type-Options"] = "nosniff"

    # 启用 XSS 过滤
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # 内容安全策略
    response.headers["Content-Security-Policy"] = "default-src 'self'"

    return response
```

---

## 安全检查清单

### 认证与授权

- [ ] 密码使用 bcrypt 等强哈希算法
- [ ] Token 有合理的过期时间
- [ ] 实现了密码错误次数限制
- [ ] 实现了账号锁定机制
- [ ] 实现了 IP 黑名单

### 输入验证

- [ ] 所有用户输入都经过验证
- [ ] 使用参数化查询防止 SQL 注入
- [ ] 对输出进行转义防止 XSS
- [ ] 验证文件上传类型和大小

### 数据保护

- [ ] 敏感数据加密存储
- [ ] 使用 HTTPS 传输
- [ ] 敏感信息脱敏显示
- [ ] 数据库访问权限最小化

### 日志与监控

- [ ] 记录登录操作
- [ ] 记录权限变更
- [ ] 记录异常错误
- [ ] 实现日志审计

---

## 练习建议

### 1. 分析项目安全特性

阅读以下文件，理解项目的安全实现：

- `module_admin/service/login_service.py` - 登录安全
- `module_admin/aspect/interface_auth.py` - 权限控制
- `utils/pwd_util.py` - 密码加密

### 2. 安全测试

```bash
# 1. 测试 SQL 注入防护
curl -X POST http://localhost:9099/api/user/add \
  -H "Content-Type: application/json" \
  -d '{"userName": "admin'"'"' OR 1=1--", "password": "123456"}'

# 2. 测试暴力破解防护
# 连续多次尝试错误密码，观察是否被锁定

# 3. 测试权限控制
# 使用普通用户 Token 访问管理员接口
```

### 3. 安全审计工具

使用工具自动检测安全问题：

- **Bandit**: Python 安全漏洞扫描
- **Safety**: 依赖包漏洞检查
- **OWASP ZAP**: Web 应用安全扫描

```bash
# 安装 Bandit
pip install bandit

# 扫描项目
bandit -r ruoyi-fastapi-backend/
```

---

## 检查清单

学完本节后，你应该能够：

- [ ] 理解认证和授权的区别
- [ ] 理解 JWT 的工作原理
- [ ] 知道常见的安全威胁（SQL注入、XSS、CSRF）
- [ ] 理解密码哈希的作用
- [ ] 知道如何验证用户输入
- [ ] 理解 HTTPS 的作用
- [ ] 知道项目中的安全防护措施
- [ ] 能够设计基本的防护策略

**恭喜！** 前置知识学习完成。现在可以进入 [第二阶段：项目实战](../02-学习路径/01-第一阶段基础篇.md)。
