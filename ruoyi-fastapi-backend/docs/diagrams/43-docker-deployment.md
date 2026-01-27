# Docker容器化部署详解

## 1. 容器化构建流程

```mermaid
flowchart TD
    Start([项目准备]) --> WriteDockerfile[编写Dockerfile]
    WriteDockerfile --> WriteCompose[编写docker-compose.yml]
    WriteCompose --> WriteEnv[编写.env配置]

    WriteDockerfile --> BuildImage[构建镜像]
    BuildImage --> DockerBuild["docker build -t app:tag"]

    DockerBuild --> PushImage{推送镜像?}
    PushImage -->|是| Registry[推送到仓库]
    PushImage -->|否| Local[本地使用]

    Registry --> PullImage["docker pull"]
    Local --> PullImage

    PullImage --> RunContainer["docker run"]
    RunContainer --> Deploy[部署应用]

    Deploy --> HealthCheck[健康检查]
    HealthCheck --> Success{运行正常?}

    Success -->|是| Complete[部署完成]
    Success -->|否| Debug[调试问题]

    Debug --> RunContainer

    style Start fill:#90EE90
    style Complete fill:#4CAF50
    style WriteDockerfile fill:#2196F3
```

## 2. Dockerfile最佳实践

```mermaid
flowchart TD
    Start([选择基础镜像]) --> Alpine{选择镜像?}

    Alpine -->|Python| PythonAlpine["python:3.11-slim"]
    Alpine -->|Node| NodeAlpine["node:18-alpine"]
    Alpine -->|Nginx| NginxAlpine["nginx:alpine"]

    PythonAlpine --> SetWorkDir["设置工作目录"]
    NodeAlpine --> SetWorkDir
    NginxAlpine --> SetWorkDir

    SetWorkDir --> CopyRequirements[复制依赖文件]
    CopyRequirements --> InstallDeps["安装依赖"]

    InstallDeps --> CopyCode[复制代码]
    CopyCode --> SetUser["设置非root用户"]

    SetUser --> ExposePort["暴露端口"]
    ExposePort --> SetCmd["设置启动命令"]

    SetCmd --> Build[构建镜像]

    style Start fill:#90EE90
    style Build fill:#4CAF50
    style PythonAlpine fill:#3776AB
```

## 3. Docker Compose编排

```mermaid
flowchart TD
    Start([启动服务]) --> ParseCompose[解析docker-compose.yml]

    ParseCompose --> CreateNetwork[创建网络]
    CreateNetwork --> CreateVolume[创建数据卷]

    CreateVolume --> StartServices[启动服务]

    StartServices --> App[应用容器]
    StartServices --> DB[数据库容器]
    StartServices --> Redis[Redis容器]
    StartServices --> Nginx[Nginx容器]

    App --> ConnectDB[连接数据库]
    App --> ConnectRedis[连接Redis]

    ConnectDB --> HealthCheck[健康检查]
    ConnectRedis --> HealthCheck

    HealthCheck --> AllOK{所有服务正常?}

    AllOK -->|是| Running[运行中]
    AllOK -->|否| Restart[重启服务]

    Restart --> HealthCheck

    Running --> Logs[查看日志]
    Logs --> Scale[扩缩容]

    Scale --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style App fill:#3776AB
    style DB fill:#4479A1
```

## 4. 多阶段构建

```mermaid
sequenceDiagram
    autonumber
    participant Builder as 🔨 构建器
    participant Deps as 📦 依赖阶段
    participant Runtime as ⚡ 运行阶段
    participant Image as 🐳 镜像

    Builder->>Deps: FROM python:3.11 AS builder
    Deps->>Deps: 安装构建工具
    Deps->>Deps: 复制依赖文件
    Deps->>Deps: pip install requirements.txt

    Builder->>Runtime: FROM python:3.11-slim AS runtime
    Runtime->>Runtime: 仅复制运行时文件
    Runtime->>Deps: COPY --from=builder /app /app
    Runtime->>Runtime: 设置环境变量
    Runtime->>Runtime: 暴露端口
    Runtime->>Runtime: 设置启动命令

    Runtime->>Image: 生成最终镜像
    Image-->>Builder: 轻量化镜像

    Note over Builder,Runtime: 镜像大小: 1GB → 100MB
```

## 5. 容器网络配置

```mermaid
graph TB
    subgraph "网络模式"
        A1[bridge 桥接网络]
        A2[host 主机网络]
        A3[overlay 覆盖网络]
        A4[none 无网络]
    end

    subgraph "容器通信"
        B1[容器间通信]
        B2[容器访问宿主]
        B3[外部访问容器]
    end

    subgraph "端口映射"
        C1["-p 80:80<br/>-p 443:443"]
        C2["-p 127.0.0.1:3306:3306"]
        C3["-p 9099:9099"]
    end

    subgraph "DNS配置"
        D1[自定义DNS]
        D2[DNS搜索域]
        D3[DNS选项]
    end

    A1 --> B1
    B1 --> C1
    C1 --> D1

    style A1 fill:#4CAF50
    style B1 fill:#2196F3
    style C1 fill:#FF9800
```

## 6. 数据持久化

```mermaid
flowchart TD
    Start([容器启动]) --> CheckVolume{使用数据卷?}

    CheckVolume -->|命名卷| CreateNamed["创建命名卷"]
    CheckVolume -->|绑定挂载| CreateBind["绑定挂载目录"]

    CreateNamed --> Mount[挂载到容器]
    CreateBind --> Mount

    Mount --> WriteData[写入数据]

    WriteData --> CheckLife{容器生命周期?}

    CheckLife -->|删除容器| PreserveData[保留数据]
    CheckLife -->|重启容器| RestoreData[恢复数据]

    PreserveData --> Backup[备份卷]
    RestoreData --> Mount

    Backup --> CleanUp[清理旧卷]
    CleanUp --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Backup fill:#FF9800
```

## 7. 容器监控与日志

```mermaid
sequenceDiagram
    autonumber
    participant App as 🐳 容器应用
    participant Docker as 🐋 Docker引擎
    participant Collector as 📊 收集器
    participant Monitor as 📈 监控系统

    App->>Docker: 产生日志
    App->>Docker: 产生指标

    Docker->>Collector: 发送日志
    Docker->>Monitor: 发送指标

    Collector->>Collector: 聚合日志
    Monitor->>Monitor: 聚合指标

    Collector->>Collector: 存储日志
    Monitor->>Monitor: 存储指标

    Monitor->>Monitor: 分析数据
    Monitor->>Monitor: 触发告警

    Monitor-->>App: 重启不健康容器

    Note over Collector: 使用ELK Stack
    Note over Monitor: 使用Prometheus+Grafana
```

## 8. 生产环境部署

```mermaid
flowchart TD
    Start([生产部署]) --> PrepareEnv[准备环境]

    PrepareEnv --> InstallDocker["安装Docker & Docker Compose"]
    PrepareEnv --> ConfigFirewall["配置防火墙"]
    PrepareEnv --> ConfigSSL["配置SSL证书"]

    InstallDocker --> CloneCode[拉取代码]
    ConfigFirewall --> CloneCode
    ConfigSSL --> CloneCode

    CloneCode --> BuildImage[构建镜像]
    BuildImage --> PushRegistry[推送到私有仓库]

    PushRegistry --> CreateCompose["创建docker-compose.prod.yml"]
    CreateCompose --> ConfigEnv["配置.env生产环境"]

    ConfigEnv --> StartServices["启动服务堆栈"]

    StartServices --> CheckHealth[检查健康状态]
    CheckHealth --> ConfigureNginx[配置Nginx反向代理]

    ConfigureNginx --> EnableHTTPS[启用HTTPS]
    EnableHTTPS --> SetupMonitor[启用监控]

    SetupMonitor --> BackupPlan[配置备份]
    BackupPlan --> DeploySuccess[部署成功]

    style Start fill:#90EE90
    style DeploySuccess fill:#4CAF50
```

## 关键配置文件

| 文件 | 用途 |
|------|------|
| `Dockerfile` | 构建镜像 |
| `docker-compose.yml` | 开发环境编排 |
| `docker-compose.prod.yml` | 生产环境编排 |
| `.dockerignore` | 排除文件 |
| `.env` | 环境变量 |

## 最佳实践

```mermaid
mindmap
    root((Docker最佳实践))
        镜像优化
            使用多阶段构建
            选择轻量级基础镜像
            合并RUN指令
            清理缓存
        安全加固
            使用非root用户
            最小化暴露端口
            定期更新基础镜像
            扫描安全漏洞
        配置管理
            环境变量注入
            配置文件外部化
            密钥管理
        资源限制
            限制CPU使用
            限制内存使用
            限制磁盘IO
        日志管理
            日志驱动配置
            日志轮转
            集中式日志收集
```
