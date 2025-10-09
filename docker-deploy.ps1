# RuoYi-Vue3-FastAPI PowerShell 部署脚本
# 使用方法: .\docker-deploy.ps1 [start|stop|restart|build|logs|clean]

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "build", "status", "logs", "clean", "backup", "restore", "help")]
    [string]$Command = "help",

    [Parameter(Position=1)]
    [string]$Service = "",

    [Parameter(Position=2)]
    [string]$BackupFile = ""
)

# 项目信息
$PROJECT_NAME = "RuoYi-Vue3-FastAPI"
$CONTAINER_PREFIX = "ruoyi-vue3-fastapi"

# 颜色定义
function Write-ColoredOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )

    Write-Host $Message -ForegroundColor $Color
}

# 日志函数
function log_info {
    param([string]$message)
    Write-ColoredOutput "[INFO] $message" "Blue"
}

function log_success {
    param([string]$message)
    Write-ColoredOutput "[SUCCESS] $message" "Green"
}

function log_warning {
    param([string]$message)
    Write-ColoredOutput "[WARNING] $message" "Yellow"
}

function log_error {
    param([string]$message)
    Write-ColoredOutput "[ERROR] $message" "Red"
}

# 检查 Docker 是否运行
function check_docker {
    try {
        docker info | Out-Null
    } catch {
        log_error "Docker 未运行，请启动 Docker Desktop"
        exit 1
    }
}

# 检查 Docker Compose 是否安装
function check_docker_compose {
    try {
        docker-compose version | Out-Null
    } catch {
        log_error "Docker Compose 未安装，请安装 Docker Compose"
        exit 1
    }
}

# 检查 .env 文件
function check_env {
    if (-not (Test-Path ".env")) {
        log_error ".env 文件不存在，请先配置环境变量"
        exit 1
    }
}

# 创建必要的目录
function create_directories {
    log_info "创建必要的目录..."

    $directories = @(
        ".\docker\postgres\init",
        ".\docker\nginx\conf.d",
        ".\docker\nginx\ssl",
        ".\conf",
        ".\logs",
        ".\uploads",
        ".\backups"
    )

    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }

    log_success "目录创建完成"
}

# 构建前端
function build_frontend {
    log_info "构建前端项目..."

    if (Test-Path "ruoyi-fastapi-frontend") {
        Set-Location "ruoyi-fastapi-frontend"

        if (-not (Test-Path "node_modules")) {
            log_info "安装前端依赖..."
            npm install --registry=https://registry.npmmirror.com
        }

        log_info "打包前端项目..."
        npm run build:prod

        Set-Location ".."
        log_success "前端构建完成"
    } else {
        log_warning "前端目录不存在，跳过前端构建"
    }
}

# 启动服务
function start_services {
    log_info "启动 $PROJECT_NAME 服务..."

    # 检查服务是否已运行
    $status = docker-compose ps
    if ($status -match "Up") {
        log_warning "服务已经在运行中"
        return
    }

    # 构建并启动服务
    docker-compose up -d --build

    # 等待服务启动
    log_info "等待服务启动..."
    Start-Sleep -Seconds 30

    # 检查服务状态
    $status = docker-compose ps
    if ($status -match "Up") {
        log_success "服务启动成功"
        show_status
    } else {
        log_error "服务启动失败"
        docker-compose logs
        exit 1
    }
}

# 停止服务
function stop_services {
    log_info "停止 $PROJECT_NAME 服务..."
    docker-compose down
    log_success "服务已停止"
}

# 重启服务
function restart_services {
    log_info "重启 $PROJECT_NAME 服务..."
    stop_services
    start_services
}

# 显示服务状态
function show_status {
    log_info "服务状态:"
    docker-compose ps
}

# 查看日志
function show_logs {
    param([string]$service = "")

    if ($service) {
        log_info "查看 $service 服务日志..."
        docker-compose logs -f --tail=100 $service
    } else {
        log_info "查看所有服务日志..."
        docker-compose logs -f --tail=100
    }
}

# 清理
function cleanup {
    log_warning "清理 Docker 资源..."

    # 停止服务
    docker-compose down

    # 删除未使用的镜像
    docker image prune -f

    # 删除未使用的卷
    docker volume prune -f

    # 删除未使用的网络
    docker network prune -f

    log_success "清理完成"
}

# 备份数据库
function backup_database {
    log_info "备份数据库..."

    $backup_dir = ".\backups"
    if (-not (Test-Path $backup_dir)) {
        New-Item -ItemType Directory -Path $backup_dir -Force | Out-Null
    }

    $backup_file = "$backup_dir\backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"

    # 从 .env 文件读取环境变量
    $env_content = Get-Content ".env"
    $postgres_user = ($env_content | Where-Object { $_ -match "POSTGRES_USER=" }) -split "=")[1]
    $postgres_db = ($env_content | Where-Object { $_ -match "POSTGRES_DB=" }) -split "=")[1]

    docker-compose exec app-postgres pg_dump -U $postgres_user $postgres_db | Out-File -FilePath $backup_file -Encoding UTF8

    log_success "数据库备份完成: $backup_file"
}

# 恢复数据库
function restore_database {
    param([string]$backup_file = "")

    if (-not $backup_file) {
        log_error "请指定备份文件路径"
        exit 1
    }

    if (-not (Test-Path $backup_file)) {
        log_error "备份文件不存在: $backup_file"
        exit 1
    }

    log_info "恢复数据库..."

    # 从 .env 文件读取环境变量
    $env_content = Get-Content ".env"
    $postgres_user = ($env_content | Where-Object { $_ -match "POSTGRES_USER=" }) -split "=")[1]
    $postgres_db = ($env_content | Where-Object { $_ -match "POSTGRES_DB=" }) -split "=")[1]

    Get-Content $backup_file | docker-compose exec -T app-postgres psql -U $postgres_user $postgres_db

    log_success "数据库恢复完成"
}

# 显示帮助信息
function show_help {
    Write-Host "RuoYi-Vue3-FastAPI PowerShell 部署脚本" -ForegroundColor Green
    Write-Host ""
    Write-Host "使用方法: .\docker-deploy.ps1 [命令] [服务名] [备份文件]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "可用命令:" -ForegroundColor Yellow
    Write-Host "  start     启动所有服务"
    Write-Host "  stop      停止所有服务"
    Write-Host "  restart   重启所有服务"
    Write-Host "  build     构建并启动服务"
    Write-Host "  status    显示服务状态"
    Write-Host "  logs      查看服务日志"
    Write-Host "  clean     清理 Docker 资源"
    Write-Host "  backup    备份数据库"
    Write-Host "  restore   恢复数据库"
    Write-Host "  help      显示此帮助信息"
    Write-Host ""
    Write-Host "示例:" -ForegroundColor Yellow
    Write-Host "  .\docker-deploy.ps1 start                    # 启动服务"
    Write-Host "  .\docker-deploy.ps1 logs app-server          # 查看应用服务日志"
    Write-Host "  .\docker-deploy.ps1 backup                   # 备份数据库"
    Write-Host "  .\docker-deploy.ps1 restore backup_file.sql  # 恢复数据库"
}

# 主函数
function main {
    param(
        [string]$command,
        [string]$service,
        [string]$backupFile
    )

    # 检查基础环境
    check_docker
    check_docker_compose
    check_env

    switch ($command) {
        "start" {
            create_directories
            start_services
        }
        "stop" {
            stop_services
        }
        "restart" {
            restart_services
        }
        "build" {
            create_directories
            build_frontend
            start_services
        }
        "status" {
            show_status
        }
        "logs" {
            show_logs $service
        }
        "clean" {
            cleanup
        }
        "backup" {
            backup_database
        }
        "restore" {
            restore_database $backupFile
        }
        "help" {
            show_help
        }
        default {
            log_error "未知命令: $command"
            show_help
            exit 1
        }
    }
}

# 运行主函数
main -command $Command -service $Service -backupFile $BackupFile