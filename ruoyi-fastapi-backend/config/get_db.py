# 导入数据库相关组件
from config.database import async_engine, AsyncSessionLocal, Base
# 导入日志工具
from utils.log_util import logger


async def get_db():
    """
    数据库会话依赖函数，用于FastAPI的依赖注入系统
    
    功能：
    - 为每个请求创建独立的数据库会话
    - 请求处理完毕后自动关闭数据库连接
    - 不同的请求使用不同的连接，确保请求隔离
    
    语法特点：
    - 使用异步上下文管理器(async with)管理数据库会话
    - 使用yield关键字创建一个异步生成器，用于FastAPI依赖注入
    
    :return: SQLAlchemy异步会话对象
    """
    # 创建数据库会话并在上下文结束时自动关闭
    async with AsyncSessionLocal() as current_db:
        # yield返回会话对象给路由函数使用
        yield current_db
        # 当请求处理完毕后，上下文管理器会自动关闭会话


async def init_create_table():
    """
    应用启动时初始化数据库连接和表结构
    
    功能：
    - 在应用启动时执行一次
    - 确保数据库表结构与模型定义一致
    - 如果表不存在则创建表
    
    语法特点：
    - 使用异步上下文管理器处理数据库连接
    - 使用SQLAlchemy的元数据创建表
    - 通过run_sync方法在异步环境中执行同步操作
    
    :return: None
    """
    # 记录初始化开始的日志
    logger.info('初始化数据库连接...')
    # 创建数据库连接并开始事务
    async with async_engine.begin() as conn:
        # 使用run_sync方法在异步环境中执行同步的表创建操作
        # Base.metadata.create_all会根据模型定义创建所有表
        await conn.run_sync(Base.metadata.create_all)
    # 记录初始化成功的日志
    logger.info('数据库连接成功')
