"""
数据库迁移脚本：将 conversation_id 和 message_id 从 INTEGER 改为 VARCHAR(36)
执行前请备份数据库！
"""
import asyncio
import os
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from urllib.parse import quote_plus
from dotenv import load_dotenv

# 加载环境变量
backend_dir = Path(__file__).parent.parent.parent
load_dotenv(backend_dir / '.env.dev')

# 设置环境变量以便 config.env 能正确读取
os.environ['APP_ENV'] = 'prod'

from config.env import DataBaseConfig

# 构建数据库连接URL
if DataBaseConfig.db_type == 'postgresql':
    ASYNC_SQLALCHEMY_DATABASE_URL = (
        f'postgresql+asyncpg://{DataBaseConfig.db_username}:{quote_plus(DataBaseConfig.db_password)}@'
        f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{DataBaseConfig.db_database}'
    )
else:
    ASYNC_SQLALCHEMY_DATABASE_URL = (
        f'mysql+asyncmy://{DataBaseConfig.db_username}:{quote_plus(DataBaseConfig.db_password)}@'
        f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{DataBaseConfig.db_database}'
    )

async def migrate():
    """执行数据库迁移"""
    engine = create_async_engine(ASYNC_SQLALCHEMY_DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        print("开始数据库迁移...")

        # 1. 修改 chat_conversation 表
        print("\n1. 修改 chat_conversation 表...")
        try:
            # 删除主键约束
            await conn.execute(text("ALTER TABLE chat_conversation DROP CONSTRAINT IF EXISTS chat_conversation_pkey"))
            print("   - 删除主键约束成功")

            # 修改列类型
            await conn.execute(text("ALTER TABLE chat_conversation ALTER COLUMN conversation_id TYPE VARCHAR(36) USING conversation_id::VARCHAR(36)"))
            print("   - 修改 conversation_id 列类型成功")

            # 重新添加主键约束
            await conn.execute(text("ALTER TABLE chat_conversation ADD PRIMARY KEY (conversation_id)"))
            print("   - 添加主键约束成功")
        except Exception as e:
            print(f"   - 错误: {e}")

        # 2. 修改 chat_message 表
        print("\n2. 修改 chat_message 表...")
        try:
            # 删除主键约束
            await conn.execute(text("ALTER TABLE chat_message DROP CONSTRAINT IF EXISTS chat_message_pkey"))
            print("   - 删除主键约束成功")

            # 修改 message_id 列类型
            await conn.execute(text("ALTER TABLE chat_message ALTER COLUMN message_id TYPE VARCHAR(36) USING message_id::VARCHAR(36)"))
            print("   - 修改 message_id 列类型成功")

            # 修改 conversation_id 列类型
            await conn.execute(text("ALTER TABLE chat_message ALTER COLUMN conversation_id TYPE VARCHAR(36) USING conversation_id::VARCHAR(36)"))
            print("   - 修改 conversation_id 列类型成功")

            # 重新添加主键约束
            await conn.execute(text("ALTER TABLE chat_message ADD PRIMARY KEY (message_id)"))
            print("   - 添加主键约束成功")
        except Exception as e:
            print(f"   - 错误: {e}")

        print("\n数据库迁移完成！")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())
