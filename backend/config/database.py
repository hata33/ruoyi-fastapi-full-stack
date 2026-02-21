# 导入SQLAlchemy异步扩展组件
from sqlalchemy.ext.asyncio import create_async_engine  # 创建异步数据库引擎
from sqlalchemy.ext.asyncio import async_sessionmaker  # 创建异步会话工厂
from sqlalchemy.ext.asyncio import AsyncAttrs  # 提供异步属性访问功能
from sqlalchemy.orm import DeclarativeBase  # SQLAlchemy声明式基类
from urllib.parse import quote_plus  # 用于URL编码特殊字符，特别是密码中的特殊字符
from config.env import DataBaseConfig  # 导入数据库配置

# 构建MySQL异步数据库连接URL
# 格式: dialect+driver://username:password@host:port/database
# asyncmy是MySQL的异步驱动
ASYNC_SQLALCHEMY_DATABASE_URL = (
    f'mysql+asyncmy://{DataBaseConfig.db_username}:{quote_plus(DataBaseConfig.db_password)}@'
    f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{DataBaseConfig.db_database}'
)
# 根据配置的数据库类型，选择不同的连接URL
if DataBaseConfig.db_type == 'postgresql':
    # 如果配置为PostgreSQL，则使用asyncpg驱动构建连接URL
    ASYNC_SQLALCHEMY_DATABASE_URL = (
        f'postgresql+asyncpg://{DataBaseConfig.db_username}:{quote_plus(DataBaseConfig.db_password)}@'
        f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{DataBaseConfig.db_database}'
    )

# 创建异步数据库引擎实例
# echo=True表示打印SQL语句，用于调试
# max_overflow: 连接池允许溢出的连接数
# pool_size: 连接池大小
# pool_recycle: 连接池中连接的回收时间(秒)
# pool_timeout: 获取连接的超时时间(秒)
async_engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL,
    echo=DataBaseConfig.db_echo,  # 是否打印SQL语句
    max_overflow=DataBaseConfig.db_max_overflow,  # 连接池允许溢出的连接数
    pool_size=DataBaseConfig.db_pool_size,  # 连接池大小
    pool_recycle=DataBaseConfig.db_pool_recycle,  # 连接池中连接的回收时间(秒)
    pool_timeout=DataBaseConfig.db_pool_timeout,  # 获取连接的超时时间(秒)
)

# 创建异步会话工厂
# autocommit=False: 不自动提交事务
# autoflush=False: 不自动刷新
# bind=async_engine: 绑定到上面创建的异步引擎
AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=async_engine, expire_on_commit=False)


# 定义ORM模型的基类
# AsyncAttrs: 提供异步属性访问功能
# DeclarativeBase: SQLAlchemy 2.0的声明式基类
class Base(AsyncAttrs, DeclarativeBase):
    """
    所有ORM模型类的基类
    
    - AsyncAttrs: 提供异步属性访问和关系加载功能
    - DeclarativeBase: SQLAlchemy 2.0的声明式映射基类
    
    所有数据库模型类都应该继承这个基类
    """
    pass
