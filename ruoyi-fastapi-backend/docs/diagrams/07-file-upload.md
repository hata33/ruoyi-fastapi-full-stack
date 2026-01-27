# 文件上传下载流程详解

## 1. 文件上传完整流程

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 用户
    participant Frontend as 🌐 前端
    participant Component as 📁 Upload 组件
    participant Controller as 🎮 上传控制器
    participant Service as 🔧 文件服务
    participant Validator as ✅ 验证器
    participant Storage as 💾 存储服务
    participant FileSys as 📂 文件系统
    participant DB as 🗄️ 数据库

    User->>Frontend: 选择文件
    Frontend->>Component: 触发上传

    Component->>Component: 客户端验证
    Component->>Component: 检查文件大小
    Component->>Component: 检查文件类型

    alt 前端验证失败
        Component-->>User: 显示错误提示
    end

    Component->>Component: 构建 FormData
    Component->>Controller: POST /common/upload<br/>Content-Type: multipart/form-data

    Controller->>Service: upload(file)

    Service->>Validator: 验证文件
    Validator->>Validator: 检查文件扩展名
    Validator->>Validator: 检查 MIME 类型
    Validator->>Validator: 检查文件大小

    alt 验证失败
        Validator-->>Service: 抛出异常
        Service-->>Controller: 返回错误
        Controller-->>Component: 400 错误
        Component-->>User: 显示错误
    end

    Validator-->>Service: 验证通过

    Service->>Service: 生成新文件名
    Service->>Service: UUID + 原始扩展名

    Service->>Service: 生成文件路径
    Service->>Service: /upload/2024/01/01/

    Service->>Storage: 保存文件
    Storage->>FileSys: 写入磁盘
    FileSys-->>Storage: 写入成功

    Storage->>DB: 保存文件记录
    DB->>DB: INSERT INTO sys_file_info

    DB-->>Service: 返回文件ID
    Service-->>Controller: 返回文件信息

    Controller-->>Component: JSON 响应
    Component-->>User: 显示上传成功
```

## 2. 文件下载流程

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 用户
    participant Frontend as 🌐 前端
    participant Controller as 🎮 控制器
    participant Service as 🔧 服务
    participant DB as 🗄️ 数据库
    participant FileSys as 📂 文件系统
    participant Security as 🔒 安全检查

    User->>Frontend: 点击下载链接
    Frontend->>Controller: GET /common/download/file_id

    Controller->>Service: download(file_id)

    Service->>DB: 查询文件信息
    DB-->>Service: 返回文件记录

    alt 文件不存在
        Service-->>Controller: 抛出异常
        Controller-->>Frontend: 404 错误
        Frontend-->>User: 显示"文件不存在"
    end

    Service->>Security: 检查权限
    Security->>Security: 验证用户登录
    Security->>Security: 检查文件访问权限

    alt 权限不足
        Security-->>Service: 抛出异常
        Service-->>Controller: 403 错误
        Controller-->>Frontend: 403 错误
        Frontend-->>User: 显示"无权访问"
    end

    Security-->>Service: 权限验证通过

    Service->>FileSys: 读取文件
    FileSys-->>Service: 返回文件流

    Service->>Service: 设置响应头
    Service->>Service: Content-Type
    Service->>Service: Content-Disposition

    Service-->>Controller: 返回文件流
    Controller-->>Frontend: 文件流
    Frontend-->>User: 触发浏览器下载
```

## 3. 图片上传与预览

```mermaid
flowchart TD
    Start([选择图片]) --> ClientValidate[客户端验证]

    ClientValidate --> CheckType{文件类型?}
    CheckType -->|非图片| TypeError[类型错误]
    CheckType -->|图片| CheckSize{文件大小?}

    CheckSize -->|> 5MB| SizeError[大小超限]
    CheckSize -->|<= 5MB| Compress{需要压缩?}

    Compress -->|是| DoCompress[压缩图片]
    Compress -->|否| UploadFile[上传文件]

    DoCompress --> UploadFile

    UploadFile --> GenerateName[生成文件名]
    GenerateName --> GeneratePath[生成路径]

    GeneratePath --> SaveFile[保存文件]
    SaveFile --> CreateThumbnail[创建缩略图]
    CreateThumbnail --> SaveDB[保存记录]

    SaveDB --> ReturnURL[返回 URL]
    ReturnURL --> Preview[前端预览]
    Preview --> End([完成])

    TypeError --> End
    SizeError --> End

    style Start fill:#90EE90
    style End fill:#FFB6C1
    style UploadFile fill:#4CAF50
    style Preview fill:#2196F3
```

## 4. 文件存储策略

```mermaid
graph TB
    subgraph "本地存储"
        Local[本地磁盘]
        LocalPath[/var/www/upload/]
        LocalFile[文件系统]
    end

    subgraph "云存储"
        OSS[阿里云 OSS]
        COS[腾讯云 COS]
        S3[AWS S3]
    end

    subgraph "存储路径策略"
        DatePath[按日期分目录<br/>/2024/01/01/]
        TypePath[按类型分目录<br/>/image/ /document/]
        HashPath[按哈希分目录<br/>/ab/cd/]
        UserPath[按用户分目录<br/>/user/123/]
    end

    subgraph "文件命名策略"
        UUIDName[UUID 命名<br/>abc-123-xyz.jpg]
        TimestampName[时间戳命名<br/>1704067200000.jpg]
        HashName[哈希命名<br/>a1b2c3d4.jpg]
        OriginalName[保留原名<br/>photo.jpg]
    end

    Local --> LocalPath
    LocalPath --> DatePath
    LocalPath --> TypePath
    LocalPath --> HashPath
    LocalPath --> UserPath

    DatePath --> LocalFile
    TypePath --> LocalFile
    HashPath --> LocalFile
    UserPath --> LocalFile

    OSS --> CloudPath[云存储路径]
    COS --> CloudPath
    S3 --> CloudPath

    CloudPath --> DatePath
    CloudPath --> TypePath

    DatePath --> UUIDName
    TypePath --> TimestampName
    HashPath --> HashName

    style Local fill:#4479A1
    style OSS fill:#FF6B00
    style COS fill:#00A4FF
    style S3 fill:#FF9900
```

## 5. 文件安全检查

```mermaid
graph TB
    UploadedFile[上传的文件] --> ExtCheck[扩展名检查]

    ExtCheck --> CheckList{在白名单?}
    CheckList -->|否| ExtError[拒绝: 非法扩展名]
    CheckList -->|是| MIMECheck[MIME 类型检查]

    MIMECheck --> CheckMIME{MIME 匹配?}
    CheckMIME -->|否| MIMEError[拒绝: 类型伪装]
    CheckMIME -->|是| SizeCheck[文件大小检查]

    SizeCheck --> CheckSize{大小超限?}
    CheckSize -->|是| SizeError[拒绝: 文件过大]
    CheckSize -->|否| ContentCheck[内容检查]

    ContentCheck --> ScanVirus[病毒扫描]
    ScanVirus --> HasVirus{有病毒?}
    HasVirus -->|是| VirusError[拒绝: 发现病毒]
    HasVirus -->|否| ImageCheck[图片内容检查]

    ImageCheck --> CheckEXIF{检查 EXIF?}
    CheckEXIF -->|是| RemoveEXIF[移除 EXIF 信息]
    CheckEXIF -->|否| Watermark[添加水印]

    RemoveEXIF --> Watermark
    Watermark --> Success[通过检查]

    ExtError --> Reject[拒绝文件]
    MIMEError --> Reject
    SizeError --> Reject
    VirusError --> Reject

    Success --> Accept[接受文件]

    style UploadedFile fill:#E3F2FD
    style Success fill:#4CAF50
    style Reject fill:#f44336
```

## 6. 分片上传流程

```mermaid
sequenceDiagram
    autonumber
    participant Client as 客户端
    participant Server as 服务器
    participant Temp as 临时目录
    participant Merger as 合并服务
    participant File as 文件系统

    Client->>Server: 初始化上传
    Server->>Server: 生成 upload_id
    Server-->>Client: 返回 upload_id

    Note over Client,Server: 分片上传
    loop 每个分片
        Client->>Client: 切分文件块
        Client->>Server: POST /upload/chunk<br/>upload_id, chunk_index, file_data
        Server->>Temp: 保存分片<br/>temp/upload_id/chunk_1
        Server-->>Client: 确认接收
    end

    Client->>Server: POST /upload/merge<br/>upload_id, total_chunks, filename
    Server->>Server: 验证所有分片
    Server->>Merger: 合并分片
    Merger->>Temp: 读取所有分片
    Merger->>Merger: 按顺序合并
    Merger->>File: 保存完整文件
    Merger->>Temp: 删除临时分片
    Merger-->>Server: 合并完成
    Server-->>Client: 上传成功
```

## 7. 文件权限控制

```mermaid
graph TB
    subgraph "公开文件"
        Public[所有用户可访问]
        Public --> NoAuth[无需认证]
        NoAuth --> PublicFile[头像、Logo等]
    end

    subgraph "登录用户"
        LoginUser[需要登录]
        LoginUser --> JWTAuth[JWT 认证]
        JWTAuth --> UserFile[用户上传文件]
    end

    subgraph "私有文件"
        Private[特定权限]
        Private --> PermissionCheck[权限检查]
        PermissionCheck --> OwnerCheck{是所有者?}
        PermissionCheck --> RoleCheck{有权限?}

        OwnerCheck -->|是| PrivateFile[私有文件]
        RoleCheck -->|是| PrivateFile
    end

    subgraph "敏感文件"
        Sensitive[敏感信息]
        Sensitive --> Encrypt[加密存储]
        Encrypt --> AuditLog[访问审计]
        AuditLog --> SecureFile[加密文件]
    end

    style Public fill:#4CAF50
    style LoginUser fill:#2196F3
    style Private fill:#FF9800
    style Sensitive fill:#f44336
```

## 8. 文件记录数据库设计

```mermaid
erDiagram
    sys_file_info {
        int file_id PK
        string file_name
        string original_name
        string file_path
        string file_type
        string file_extension
        int file_size
        string mime_type
        int user_id FK
        string md5
        string sha256
        datetime create_time
        int download_count
        int is_deleted
    }

    sys_user {
        int user_id PK
        string user_name
    }

    sys_user ||--o{ sys_file_info : "上传"
```

## 9. 常见文件类型处理

```mermaid
mindmap
    root((文件类型处理))
        图片
            验证: jpg, png, gif, webp
            压缩: 降低质量
            缩略图: 生成多个尺寸
            水印: 添加版权信息
            EXIF: 移除敏感信息
        文档
            验证: pdf, doc, docx, xls, xlsx
            预览: 生成缩略图或PDF
            索引: 提取文本内容
            加密: 敏感文档加密
        视频
            验证: mp4, avi, mov
            转码: 统一格式
            截图: 生成封面图
            压缩: 降低码率
        压缩包
            验证: zip, rar, 7z
            扫描: 病毒检查
            解压: 检查内容
            大小: 解压后大小限制
        代码
            验证: py, js, java, etc
            语法: 检查语法
            安全: 扫描恶意代码
            加密: 保护源代码
```

## 10. 文件清理策略

```mermaid
graph TB
    Start([定时任务启动]) --> CheckTemp[检查临时文件]

    CheckTemp --> TempExpire{超过24小时?}
    TempExpire -->|是| DeleteTemp[删除临时文件]
    TempExpire -->|否| CheckUnused

    DeleteTemp --> CheckUnused[检查未使用文件]

    CheckUnused --> UnusedDays{超过30天未访问?}
    UnusedDays -->|是| ArchiveFile[归档文件]
    UnusedDays -->|否| CheckOrphan

    ArchiveFile --> MoveToArchive[移动到归档目录]
    MoveToArchive --> CheckOrphan[检查孤立文件]

    CheckOrphan --> OrphanCheck{数据库无记录?}
    OrphanCheck -->|是| DeleteOrphan[删除孤立文件]
    OrphanCheck -->|否| CheckDuplicate

    DeleteOrphan --> CheckDuplicate[检查重复文件]

    CheckDuplicate --> MD5Check{MD5 相同?}
    MD5Check -->|是| KeepOne[保留一个副本]
    MD5Check -->|否| LogReport[生成清理报告]

    KeepOne --> LogReport
    LogReport --> End([任务完成])

    style Start fill:#90EE90
    style End fill:#FFB6C1
    style DeleteTemp fill:#f44336
    style ArchiveFile fill:#FF9800
    style KeepOne fill:#4CAF50
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 文件上传控制器 | `module_admin/controller/common_controller.py` |
| 文件服务 | `module_admin/service/file_service.py` |
| 文件信息模型 | `module_admin/entity/do/file_info_do.py` |
| 文件验证 | `common/utils/file_validator.py` |
| 存储配置 | `config/file_config.py` |
| 临时文件清理 | `module_admin/task/file_cleanup_task.py` |

## 文件上传配置

```python
# 支持的文件类型
ALLOWED_EXTENSIONS = {
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
    'document': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'],
    'video': ['.mp4', '.avi', '.mov', '.wmv'],
    'archive': ['.zip', '.rar', '.7z']
}

# 文件大小限制（字节）
MAX_FILE_SIZE = {
    'image': 5 * 1024 * 1024,      # 5MB
    'document': 10 * 1024 * 1024,  # 10MB
    'video': 100 * 1024 * 1024,    # 100MB
    'archive': 50 * 1024 * 1024     # 50MB
}

# 存储路径配置
UPLOAD_PATH = '/var/www/upload/'
TEMP_PATH = '/var/www/temp/'
ARCHIVE_PATH = '/var/www/archive/'
```
