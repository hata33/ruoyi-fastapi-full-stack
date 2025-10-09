#!/bin/bash
set -e

# PostgreSQL 数据库初始化脚本
# 此脚本会在 PostgreSQL 容器首次启动时自动执行

echo "开始初始化 PostgreSQL 数据库..."

# 等待 PostgreSQL 服务完全启动
until pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}; do
    echo "等待 PostgreSQL 启动..."
    sleep 2
done

echo "PostgreSQL 已启动，开始执行初始化脚本..."

# 检查是否已经初始化过
INIT_CHECK=$(psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -tAc "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'sys_user')")

if [ "$INIT_CHECK" = "t" ]; then
    echo "数据库已经初始化过，跳过初始化步骤"
else
    echo "开始执行数据库初始化..."

    # 执行 SQL 初始化脚本
    if [ -f "/docker-entrypoint-initdb.d/sql/ruoyi-fastapi-pg.sql" ]; then
        echo "执行 PostgreSQL 初始化脚本..."
        psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -f /docker-entrypoint-initdb.d/sql/ruoyi-fastapi-pg.sql
        echo "PostgreSQL 数据库初始化完成"
    elif [ -f "/docker-entrypoint-initdb.d/sql/ruoyi-fastapi.sql" ]; then
        echo "执行 MySQL 初始化脚本（需要转换）..."
        # 注意：MySQL 脚本需要手动转换为 PostgreSQL 语法
        echo "警告：检测到 MySQL SQL 脚本，请手动转换为 PostgreSQL 语法"
    else
        echo "警告：未找到 SQL 初始化脚本"
    fi
fi

echo "数据库初始化脚本执行完成"