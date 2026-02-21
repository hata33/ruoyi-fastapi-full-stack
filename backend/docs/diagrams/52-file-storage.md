# 文件存储方案详解

## 1. 文件上传流程

```mermaid
sequenceDiagram
    autonumber
    participant Client as 📱 客户端
    participant API as 🌐 API网关
    participant Validator as ✅ 验证器
    participant Storage as 📦 存储服务
    participant DB as 🗄️ 数据库
    participant CDN as 🌐 CDN

    Client->>API: 上传文件请求
    API->>Validator: 验证请求

    alt 验证失败
        Validator-->>API: 返回错误
        API-->>Client: 拒绝上传
    else 验证成功
        Validator->>API: 验证通过
        API->>Storage: 上传文件

        Storage->>Storage: 生成文件名
        Storage->>Storage: 计算文件哈希
        Storage->>Storage: 保存文件

        Storage->>CDN: 同步到CDN
        CDN-->>Storage: 同步完成

        Storage-->>API: 返回文件信息
        API->>DB: 保存文件记录
        DB-->>API: 保存成功

        API-->>Client: 返回文件URL
    end

    Note over Validator: 验证:<br/>- 文件类型<br/>- 文件大小<br/>- 权限检查
```

## 2. 本地文件存储

```mermaid
flowchart TD
    Start([文件上传]) --> CheckConfig{配置存储}

    CheckConfig -->|本地| LocalStorage[本地存储]
    CheckConfig -->|云| CloudStorage[云存储]

    LocalStorage --> GetBasePath[获取基础路径]
    GetBasePath --> GenerateDir[生成目录]

    GenerateDir --> DateDir["按日期: /upload/2024/01/"]
    GenerateDir --> TypeDir["按类型: /upload/image/"]
    GenerateDir --> UserDir["按用户: /upload/user/123/"]

    DateDir --> CreatePath[创建完整路径]
    TypeDir --> CreatePath
    UserDir --> CreatePath

    CreatePath --> Mkdir[创建目录]
    Mkdir --> GenerateName[生成文件名]

    GenerateName --> UUIDName["UUID.jpg"]
    GenerateName --> HashName["MD5哈希.jpg"]
    GenerateName --> TimestampName["时间戳.jpg"]

    UUIDName --> SaveFile[保存文件]
    HashName --> SaveFile
    TimestampName --> SaveFile

    SaveFile --> WriteDisk[写入磁盘]
    WriteDisk --> Success{成功?}

    Success -->|否| Retry[重试]
    Success -->|是| SetPermission[设置权限]

    Retry --> SaveFile

    SetPermission --> Chmod["chmod 644"]
    Chmod --> GenerateURL[生成URL]

    GenerateURL --> RelativePath["相对路径"]
    GenerateURL --> AbsolutePath["绝对路径"]
    GenerateURL --> FullURL["完整URL"]

    RelativePath --> Return[返回信息]
    AbsolutePath --> Return
    FullURL --> Return

    Return --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style LocalStorage fill:#2196F3
```

## 3. 云存储集成

```mermaid
flowchart TD
    Start([文件上传]) --> SelectProvider{选择提供商}

    SelectProvider --> AWS[AWS S3]
    SelectProvider --> Aliyun[阿里云OSS]
    SelectProvider --> Tencent[腾讯云COS]
    SelectProvider --> Qiniu[七牛云]

    AWS --> InitClient[初始化客户端]
    Aliyun --> InitClient
    Tencent --> InitClient
    Qiniu --> InitClient

    InitClient --> LoadConfig[加载配置]
    LoadConfig --> AccessKey[访问密钥]
    LoadConfig --> SecretKey[密钥]
    LoadConfig --> Bucket[存储桶]
    LoadConfig --> Region[区域]

    AccessKey --> CreateBucket
    SecretKey --> CreateBucket
    Bucket --> CreateBucket
    Region --> CreateBucket

    CreateBucket[创建桶连接] --> Upload[上传文件]

    Upload --> SetMetadata[设置元数据]
    SetMetadata --> ContentType[Content-Type]
    SetMetadata --> CacheControl[Cache-Control]
    SetMetadata --> CustomMeta[自定义元数据]

    ContentType --> ProcessUpload
    CacheControl --> ProcessUpload
    CustomMeta --> ProcessUpload

    ProcessUpload[执行上传] --> Multipart{大文件?}

    Multipart -->|是| MultipartUpload[分片上传]
    Multipart -->|否| SimpleUpload[简单上传]

    SimpleUpload --> GetURL[获取URL]
    MultipartUpload --> GetURL

    GetURL --> PublicURL[公读URL]
    GetURL --> SignedURL[签名URL]
    GetURL --> CDNURL[CDN加速URL]

    PublicURL --> End([返回URL])
    SignedURL --> End
    CDNURL --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style SelectProvider fill:#FF9800
```

## 4. 文件分片上传

```mermaid
sequenceDiagram
    autonumber
    participant Client as 📱 客户端
    participant Server as 🌐 服务器
    participant Storage as 📦 存储
    participant DB as 🗄️ 数据库

    Client->>Server: 初始化上传
    Server->>DB: 创建上传记录
    DB-->>Server: 返回uploadID
    Server-->>Client: 返回uploadID

    Client->>Client: 分片文件
    Note over Client: 分片1: 0-5MB<br/>分片2: 5-10MB<br/>分片3: 10-15MB

    loop 上传分片
        Client->>Server: 上传分片 + uploadID
        Server->>Storage: 存储分片
        Storage-->>Server: 返回ETag
        Server->>DB: 记录分片信息
        Server-->>Client: 确认分片
    end

    Client->>Server: 完成上传
    Server->>DB: 检查所有分片
    DB-->>Server: 所有分片已上传

    Server->>Storage: 合并分片
    Storage->>Storage: 按顺序合并
    Storage->>Storage: 验证完整性
    Storage-->>Server: 合并完成

    Server->>DB: 更新文件状态
    DB-->>Server: 更新成功
    Server-->>Client: 上传完成

    Note over Storage: 并行上传<br/>断点续传
```

## 5. 图片处理服务

```mermaid
flowchart TD
    Start([图片上传]) --> DetectType{检测类型}

    DetectType --> Image[图片]
    DetectType --> Video[视频]
    DetectType --> Document[文档]

    Image --> ImageProcess[图片处理]
    Video --> VideoProcess[视频处理]
    Document --> DocumentProcess[文档处理]

    ImageProcess --> Resize[调整大小]
    ImageProcess --> Crop[裁剪]
    ImageProcess --> Rotate[旋转]
    ImageProcess --> Watermark[水印]
    ImageProcess --> Compress[压缩]
    ImageProcess --> Format[格式转换]

    Resize --> Variants[生成多规格]
    Crop --> Variants
    Watermark --> Variants
    Compress --> Variants
    Format --> Variants

    Variants --> Thumb[缩略图]
    Variants --> Small[小图]
    Variants --> Medium[中图]
    Variants --> Large[大图]
    Variants --> Original[原图]

    Thumb --> SaveAll[保存所有规格]
    Small --> SaveAll
    Medium --> SaveAll
    Large --> SaveAll
    Original --> SaveAll

    SaveAll --> GenerateURL[生成URL]
    GenerateURL --> End([完成])

    VideoProcess --> ExtractFrame[提取封面]
    VideoProcess --> Transcode[转码]

    DocumentProcess --> Preview[生成预览]
    DocumentProcess --> Index[全文索引]

    ExtractFrame --> End
    Transcode --> End
    Preview --> End
    Index --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style ImageProcess fill:#FF9800
```

## 6. 文件访问控制

```mermaid
flowchart TD
    Start([文件请求]) --> CheckAuth{验证身份}

    CheckAuth -->|未认证| PublicFile{公开文件?}
    CheckAuth -->|已认证| UserAccess[用户访问]

    PublicFile -->|是| ReturnPublic[返回公开文件]
    PublicFile -->|否| Return401[返回401]

    UserAccess --> CheckPermission{检查权限}

    CheckPermission -->|所有者| FullAccess[完全访问]
    CheckPermission -->|授权读者| ReadOnly[只读访问]
    CheckPermission -->|无权限| Return403[返回403]

    FullAccess --> DirectAccess[直接访问]
    ReadOnly --> DirectAccess
    ReturnPublic --> DirectAccess

    DirectAccess --> CheckMethod{请求方法?}

    CheckMethod -->|GET| Download[下载文件]
    CheckMethod -->|HEAD| GetMeta[获取元信息]
    CheckMethod -->|DELETE| DeleteFile[删除文件]
    CheckMethod -->|PUT| UpdateFile[更新文件]

    Download --> RangeSupport{支持Range?}
    RangeSupport -->|是| PartialContent[分段下载]
    RangeSupport -->|否| FullContent[完整下载]

    PartialContent --> Stream[流式传输]
    FullContent --> Stream

    GetMeta --> ReturnMeta[返回元数据]
    DeleteFile --> SoftDelete[软删除]
    UpdateFile --> VersionControl[版本控制]

    Stream --> LogAccess[记录访问]
    ReturnMeta --> LogAccess
    SoftDelete --> LogAccess
    VersionControl --> LogAccess

    LogAccess --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style CheckPermission fill:#FF9800
```

## 7. 文件清理策略

```mermaid
flowchart TD
    Start([定时任务]) --> ScanFiles[扫描文件]

    ScanFiles --> CheckTemp[检查临时文件]
    ScanFiles --> CheckExpired[检查过期文件]
    ScanFiles --> CheckOrphan[检查孤儿文件]

    CheckTemp --> TempPolicy[临时文件策略]
    CheckExpired --> ExpiredPolicy[过期策略]
    CheckOrphan --> OrphanPolicy[孤儿策略]

    TempPolicy --> TimeRule["24小时后删除"]
    ExpiredPolicy --> ExpireRule["超过保留期删除"]
    OrphanPolicy --> RefRule["无引用删除"]

    TimeRule --> MarkDelete[标记删除]
    ExpireRule --> MarkDelete
    RefRule --> MarkDelete

    MarkDelete --> Verify[验证可删除]
    Verify --> DoubleCheck{二次确认}

    DoubleCheck -->|引用存在| Cancel[取消删除]
    DoubleCheck -->|可安全删除| ExecuteDelete[执行删除]

    ExecuteDelete --> DeleteFromStorage[从存储删除]
    DeleteFromStorage --> DeleteFromDB[从数据库删除]

    DeleteFromDB --> RecordLog[记录日志]
    RecordLog --> UpdateStats[更新统计]

    UpdateStats --> Report[生成报告]
    Report --> Notify[通知管理员]

    Cancel --> End([完成])
    Notify --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style ExecuteDelete fill:#FF6B6B
```

## 8. CDN加速配置

```mermaid
mindmap
    root((CDN加速))
        节点选择
            就近接入
            智能路由
            负载均衡
            故障切换
        缓存策略
            缓存规则
            缓存时长
            缓存刷新
            缓存预热
        安全防护
            HTTPS加速
            防盗链
            IP黑白名单
            URL鉴权
        性能优化
            图片优化
            压缩传输
            协议优化
            预加载
        监控统计
            流量统计
            命中率
            响应时间
            错误率
        成本控制
            流量包
            带宽峰值
            请求数
            区域定价
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 文件上传 | `module_admin/controller/upload_controller.py` |
| 存储服务 | `services/file_storage_service.py` |
| OSS配置 | `config/storage.py` |
| 前端上传 | `src/components/upload/` |

## 最佳实践

```mermaid
flowchart LR
    subgraph "上传优化"
        A1[分片上传]
        A2[断点续传]
        A3[并发上传]
        A4[压缩传输]
    end

    subgraph "存储优化"
        B1[冷热分离]
        B2[多副本]
        B3[去重]
        B4[生命周期]
    end

    subgraph "访问优化"
        C1[CDN加速]
        C2[就近访问]
        C3[协议优化]
        C4[缓存策略]
    end

    A1 --> Practice[实施]
    B1 --> Practice
    C1 --> Practice

    style A1 fill:#4CAF50
    style B1 fill:#FF9800
    style C1 fill:#2196F3
```
