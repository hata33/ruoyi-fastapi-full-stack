# 导入Redis异步客户端库
from redis import asyncio as aioredis  # 使用Redis的异步IO支持
# 导入Redis异常类，用于异常处理
from redis.exceptions import AuthenticationError, TimeoutError, RedisError
# 导入数据库会话工厂，用于创建数据库会话
from config.database import AsyncSessionLocal
# 导入Redis配置参数
from config.env import RedisConfig
# 导入系统配置服务，用于缓存系统配置
from module_admin.service.config_service import ConfigService
# 导入字典数据服务，用于缓存字典数据
from module_admin.service.dict_service import DictDataService
# 导入日志工具
from utils.log_util import logger


class RedisUtil:
    """
    Redis工具类：管理Redis连接和系统缓存
    
    设计目的：
    1. 集中管理Redis连接的创建和关闭
    2. 提供系统启动时初始化缓存的方法
    3. 使用类方法模式，避免实例化，方便全局调用
    4. 异步实现，符合FastAPI异步框架特性
    """

    @classmethod
    async def create_redis_pool(cls) -> aioredis.Redis:
        """
        创建Redis连接池
        
        设计原因：
        1. 使用连接池而非单一连接，提高并发性能
        2. 应用启动时初始化，避免每次请求创建连接
        3. 使用异步方式，不阻塞主线程
        4. 详细的异常处理和日志记录，便于问题诊断
        
        :return: Redis连接对象
        """
        # 记录连接开始的日志
        logger.info('开始连接redis...')
        # 使用from_url方法创建Redis连接
        # 从配置中读取连接参数，便于环境切换
        redis = await aioredis.from_url(
            url=f'redis://{RedisConfig.redis_host}',  # Redis服务器地址
            port=RedisConfig.redis_port,              # Redis服务器端口
            username=RedisConfig.redis_username,      # Redis用户名(如果有)
            password=RedisConfig.redis_password,      # Redis密码
            db=RedisConfig.redis_database,            # 使用的数据库索引
            encoding='utf-8',                         # 编码方式
            decode_responses=True,                    # 自动解码响应，返回Python字符串而非字节
        )
        # 测试连接是否成功
        try:
            # ping命令用于测试连接是否活跃
            connection = await redis.ping()
            if connection:
                logger.info('redis连接成功')
            else:
                logger.error('redis连接失败')
        # 捕获并记录可能的连接异常
        except AuthenticationError as e:
            # 认证错误，通常是用户名或密码错误
            logger.error(f'redis用户名或密码错误，详细错误信息：{e}')
        except TimeoutError as e:
            # 连接超时，可能是网络问题或Redis服务未启动
            logger.error(f'redis连接超时，详细错误信息：{e}')
        except RedisError as e:
            # 其他Redis错误
            logger.error(f'redis连接错误，详细错误信息：{e}')
        # 返回Redis连接对象，即使连接失败也返回对象，由调用方处理
        return redis

    @classmethod
    async def close_redis_pool(cls, app):
        """
        关闭Redis连接池
        
        设计原因：
        1. 应用关闭时优雅地释放资源，避免连接泄漏
        2. 通过app.state存储redis对象，符合FastAPI最佳实践
        3. 使用异步关闭，确保所有操作完成后再关闭连接
        
        :param app: FastAPI应用实例，包含state.redis属性
        :return: None
        """
        # 异步关闭Redis连接
        await app.state.redis.close()
        # 记录关闭成功的日志
        logger.info('关闭redis连接成功')

    @classmethod
    async def init_sys_dict(cls, redis):
        """
        初始化系统字典缓存
        
        设计原因：
        1. 将常用字典数据预加载到Redis，提高访问速度
        2. 应用启动时一次性加载，避免运行时频繁查询数据库
        3. 使用异步上下文管理器处理数据库会话，确保资源正确释放
        4. 将缓存逻辑委托给专门的服务类，符合单一职责原则
        
        :param redis: Redis连接对象
        :return: None
        """
        # 调用链：
        #   应用启动 -> 创建 Redis 连接 -> init_sys_dict(redis)
        #   -> 创建 AsyncSession -> DictDataService.init_cache_sys_dict_services(session, redis)
        #   -> 清空旧的 sys_dict:* -> 逐类 dict_type 查询并写入 Redis
        # 创建异步数据库会话，用于一次性拉取全部字典相关数据
        async with AsyncSessionLocal() as session:
            # 调用字典服务的缓存初始化方法
            # 传入数据库会话和Redis连接，实现数据从数据库到Redis的加载
            await DictDataService.init_cache_sys_dict_services(session, redis)

    @classmethod
    async def init_sys_config(cls, redis):
        """
        初始化系统配置缓存
        
        设计原因：
        1. 将系统配置参数预加载到Redis，提供快速访问
        2. 集中管理配置，便于全局使用和动态更新
        3. 与init_sys_dict方法类似，但处理不同类型的数据
        4. 遵循相同的异步模式和资源管理模式
        
        :param redis: Redis连接对象
        :return: None
        """
        # 创建异步数据库会话
        async with AsyncSessionLocal() as session:
            # 调用配置服务的缓存初始化方法
            # 将系统配置从数据库加载到Redis缓存
            await ConfigService.init_cache_sys_config_services(session, redis)
