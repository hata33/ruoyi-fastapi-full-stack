#!/bin/bash

# RuoYi-Vue3-FastAPI Docker 部署脚本
# 使用方法: ./docker-deploy.sh [start|stop|restart|build|logs|clean]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目信息
PROJECT_NAME="RuoYi-Vue3-FastAPI"
CONTAINER_PREFIX="ruoyi-vue3-fastapi"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 是否运行
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker 未运行，请启动 Docker"
        exit 1
    fi
}

# 检查 Docker Compose 是否安装
check_docker_compose() {
    if ! command -v docker-compose > /dev/null 2>&1; then
        log_error "Docker Compose 未安装，请安装 Docker Compose"
        exit 1
    fi
}

# 检查 .env 文件
check_env() {
    if [ ! -f .env ]; then
        log_error ".env 文件不存在，请先配置环境变量"
        exit 1
    fi
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    mkdir -p ./docker/postgres/init
    mkdir -p ./docker/nginx/conf.d
    mkdir -p ./docker/nginx/ssl
    mkdir -p ./conf
    mkdir -p ./logs
    mkdir -p ./uploads
    log_success "目录创建完成"
}

# 构建前端
build_frontend() {
    log_info "构建前端项目..."
    if [ -d "ruoyi-fastapi-frontend" ]; then
        cd ruoyi-fastapi-frontend
        if [ ! -d "node_modules" ]; then
            log_info "安装前端依赖..."
            npm install --registry=https://registry.npmmirror.com
        fi
        log_info "打包前端项目..."
        npm run build:prod
        cd ..
        log_success "前端构建完成"
    else
        log_warning "前端目录不存在，跳过前端构建"
    fi
}

# 启动服务
start_services() {
    log_info "启动 ${PROJECT_NAME} 服务..."

    # 检查服务是否已运行
    if docker-compose ps | grep -q "Up"; then
        log_warning "服务已经在运行中"
        return 0
    fi

    # 构建并启动服务
    docker-compose up -d --build

    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30

    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        log_success "服务启动成功"
        show_status
    else
        log_error "服务启动失败"
        docker-compose logs
        exit 1
    fi
}

# 停止服务
stop_services() {
    log_info "停止 ${PROJECT_NAME} 服务..."
    docker-compose down
    log_success "服务已停止"
}

# 重启服务
restart_services() {
    log_info "重启 ${PROJECT_NAME} 服务..."
    stop_services
    start_services
}

# 显示服务状态
show_status() {
    log_info "服务状态:"
    docker-compose ps
}

# 查看日志
show_logs() {
    local service=$1
    if [ -z "$service" ]; then
        log_info "查看所有服务日志..."
        docker-compose logs -f --tail=100
    else
        log_info "查看 $service 服务日志..."
        docker-compose logs -f --tail=100 "$service"
    fi
}

# 清理
cleanup() {
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
backup_database() {
    log_info "备份数据库..."
    local backup_dir="./backups"
    mkdir -p "$backup_dir"
    local backup_file="$backup_dir/backup_$(date +%Y%m%d_%H%M%S).sql"

    docker-compose exec app-postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > "$backup_file"
    log_success "数据库备份完成: $backup_file"
}

# 恢复数据库
restore_database() {
    local backup_file=$1
    if [ -z "$backup_file" ]; then
        log_error "请指定备份文件路径"
        exit 1
    fi

    if [ ! -f "$backup_file" ]; then
        log_error "备份文件不存在: $backup_file"
        exit 1
    fi

    log_info "恢复数据库..."
    docker-compose exec -T app-postgres psql -U ${POSTGRES_USER} ${POSTGRES_DB} < "$backup_file"
    log_success "数据库恢复完成"
}

# 显示帮助信息
show_help() {
    echo "RuoYi-Vue3-FastAPI Docker 部署脚本"
    echo ""
    echo "使用方法: $0 [命令]"
    echo ""
    echo "可用命令:"
    echo "  start     启动所有服务"
    echo "  stop      停止所有服务"
    echo "  restart   重启所有服务"
    echo "  build     构建并启动服务"
    echo "  status    显示服务状态"
    echo "  logs      查看服务日志"
    echo "  clean     清理 Docker 资源"
    echo "  backup    备份数据库"
    echo "  restore   恢复数据库"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start                    # 启动服务"
    echo "  $0 logs app-server          # 查看应用服务日志"
    echo "  $0 backup                   # 备份数据库"
    echo "  $0 restore backup_file.sql  # 恢复数据库"
}

# 主函数
main() {
    local command=$1

    # 检查基础环境
    check_docker
    check_docker_compose
    check_env

    case $command in
        start)
            create_directories
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        build)
            create_directories
            build_frontend
            start_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs $2
            ;;
        clean)
            cleanup
            ;;
        backup)
            backup_database
            ;;
        restore)
            restore_database $2
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"