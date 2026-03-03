"""
初始化 Chat 模块数据
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from module_chat.entity.do.chat_model_do import ChatModel


async def init_chat_data():
    """初始化 Chat 模块数据"""

    # 创建数据库连接
    from config.env import DataBaseConfig

    database_url = f"{DataBaseConfig.db_type}+asyncpg://{DataBaseConfig.db_username}:{DataBaseConfig.db_password}@{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{DataBaseConfig.db_database}"

    engine = create_async_engine(database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 插入模型数据
        models = [
            ChatModel(
                model_code="deepseek-chat",
                model_name="DeepSeek Chat",
                model_type="chat",
                max_tokens=64000,
                is_enabled=True,
                sort_order=1
            ),
            ChatModel(
                model_code="deepseek-reasoner",
                model_name="DeepSeek Reasoner",
                model_type="reasoner",
                max_tokens=64000,
                is_enabled=True,
                sort_order=2
            )
        ]

        for model in models:
            session.add(model)

        await session.commit()
        print("模型数据初始化成功！")


if __name__ == "__main__":
    asyncio.run(init_chat_data())
