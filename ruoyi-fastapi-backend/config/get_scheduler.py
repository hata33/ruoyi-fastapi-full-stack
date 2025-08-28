import json
from apscheduler.events import EVENT_ALL
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from asyncio import iscoroutinefunction
from datetime import datetime, timedelta
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Union
from config.database import AsyncSessionLocal, quote_plus
from config.env import DataBaseConfig, RedisConfig
from module_admin.dao.job_dao import JobDao
from module_admin.entity.vo.job_vo import JobLogModel, JobModel
from module_admin.service.job_log_service import JobLogService
from utils.log_util import logger
import module_task  # noqa: F401


# 重写Cron定时触发器，扩展标准CronTrigger的功能
class MyCronTrigger(CronTrigger):
    @classmethod
    def from_crontab(cls, expr: str, timezone=None):
        """
        从crontab表达式创建Cron触发器
        
        支持扩展的crontab格式，包括：
        - 工作日标识(W)：如15W表示15号最近的工作日
        - 最后一天标识(L)：如L表示月份最后一天
        - 第N个星期几标识(#)：如6#3表示第3个星期五
        
        :param expr: crontab表达式字符串
        :param timezone: 时区设置
        :return: 配置好的CronTrigger对象
        """
        # 按空格分割crontab表达式
        values = expr.split()
        
        # 验证字段数量：标准cron是6个字段，扩展cron是7个字段
        if len(values) != 6 and len(values) != 7:
            raise ValueError('Wrong number of fields; got {}, expected 6 or 7'.format(len(values)))

        # 解析各个时间字段
        second = values[0]      # 秒
        minute = values[1]      # 分钟
        hour = values[2]        # 小时
        
        # 处理日期字段，支持特殊标识符
        if '?' in values[3]:
            day = None  # ?表示不指定日期
        elif 'L' in values[5]:
            # L表示最后一天，如5L表示5号是最后一天
            day = f"last {values[5].replace('L', '')}"
        elif 'W' in values[3]:
            # W表示工作日，如15W表示15号最近的工作日
            day = cls.__find_recent_workday(int(values[3].split('W')[0]))
        else:
            # 普通日期，移除L标识符
            day = values[3].replace('L', 'last')
        
        month = values[4]       # 月份
        
        # 处理星期字段，支持特殊标识符
        if '?' in values[5] or 'L' in values[5]:
            week = None  # ?或L表示不指定星期
        elif '#' in values[5]:
            # #表示第N个星期几，如6#3表示第3个星期五
            week = int(values[5].split('#')[1])
        else:
            week = values[5]    # 普通星期
        
        # 处理星期几字段
        if '#' in values[5]:
            # 提取星期几的数字，减1是因为cron中星期从0开始
            day_of_week = int(values[5].split('#')[0]) - 1
        else:
            day_of_week = None
        
        # 年份字段（可选）
        year = values[6] if len(values) == 7 else None
        
        # 返回配置好的CronTrigger对象
        return cls(
            second=second,
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            week=week,
            day_of_week=day_of_week,
            year=year,
            timezone=timezone,
        )

    @classmethod
    def __find_recent_workday(cls, day: int):
        """
        查找指定日期最近的工作日
        
        如果指定日期是周末，则向前查找最近的工作日
        
        :param day: 指定的日期
        :return: 最近的工作日
        """
        now = datetime.now()
        date = datetime(now.year, now.month, day)
        
        # 如果指定日期是工作日（周一到周五），直接返回
        if date.weekday() < 5:
            return date.day
        else:
            # 如果是周末，向前查找最近的工作日
            diff = 1
            while True:
                previous_day = date - timedelta(days=diff)
                if previous_day.weekday() < 5:  # 找到工作日
                    return previous_day.day
                else:
                    diff += 1  # 继续向前查找


# 构建数据库连接URL
# 根据配置的数据库类型选择不同的连接字符串格式
SQLALCHEMY_DATABASE_URL = (
    f'mysql+pymysql://{DataBaseConfig.db_username}:{quote_plus(DataBaseConfig.db_password)}@'
    f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{DataBaseConfig.db_database}'
)

# 如果是PostgreSQL数据库，使用不同的连接格式
if DataBaseConfig.db_type == 'postgresql':
    SQLALCHEMY_DATABASE_URL = (
        f'postgresql+psycopg2://{DataBaseConfig.db_username}:{quote_plus(DataBaseConfig.db_password)}@'
        f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{DataBaseConfig.db_database}'
    )

# 创建SQLAlchemy数据库引擎
# 用于APScheduler的SQLAlchemyJobStore存储任务信息
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=DataBaseConfig.db_echo,                    # 是否打印SQL语句
    max_overflow=DataBaseConfig.db_max_overflow,    # 连接池最大溢出连接数
    pool_size=DataBaseConfig.db_pool_size,          # 连接池大小
    pool_recycle=DataBaseConfig.db_pool_recycle,    # 连接回收时间
    pool_timeout=DataBaseConfig.db_pool_timeout,    # 连接超时时间
)

# 创建数据库会话工厂
# 用于在事件监听器中记录任务执行日志
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 配置任务存储后端
# 支持多种存储方式，提供灵活性和可靠性
job_stores = {
    'default': MemoryJobStore(),  # 默认内存存储，快速但重启后丢失
    'sqlalchemy': SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URL, engine=engine),  # 数据库存储，持久化
    'redis': RedisJobStore(  # Redis存储，支持分布式部署
        **dict(
            host=RedisConfig.redis_host,
            port=RedisConfig.redis_port,
            username=RedisConfig.redis_username,
            password=RedisConfig.redis_password,
            db=RedisConfig.redis_database,
        )
    ),
}

# 配置任务执行器
# 支持不同类型的任务执行方式
executors = {
    'default': AsyncIOExecutor(),           # 默认异步IO执行器，适合I/O密集型任务
    'processpool': ProcessPoolExecutor(5)   # 进程池执行器，适合CPU密集型任务，最大5个进程
}

# 配置任务默认参数
# 这些参数会应用到所有新创建的任务上
job_defaults = {
    'coalesce': False,      # 是否合并错过的任务执行
    'max_instance': 1       # 每个任务的最大并发实例数
}

# 创建异步IO调度器实例
scheduler = AsyncIOScheduler()

# 配置调度器，设置存储、执行器和默认参数
scheduler.configure(jobstores=job_stores, executors=executors, job_defaults=job_defaults)


class SchedulerUtil:
    """
    定时任务相关方法
    """

    @classmethod
    async def init_system_scheduler(cls):
        """
        应用启动时初始化定时任务
        
        这个方法在应用启动时被调用，主要完成以下工作：
        1. 启动APScheduler调度器
        2. 从数据库加载所有启用的定时任务
        3. 清理可能存在的重复任务
        4. 重新注册所有任务到调度器
        5. 添加事件监听器用于监控任务执行状态
        
        :return: 无返回值
        """
        # 记录启动日志
        logger.info('开始启动定时任务...')
        
        # 启动APScheduler调度器，开始接受任务调度
        scheduler.start()
        
        # 使用异步数据库会话获取任务列表
        async with AsyncSessionLocal() as session:
            # 从数据库获取所有状态为启用(status='0')的定时任务
            # 这些任务在应用重启前就已经配置好了
            job_list = await JobDao.get_job_list_for_scheduler(session)
            
            # 遍历每个任务，确保没有重复注册
            for item in job_list:
                # 先移除可能存在的同名任务，避免重复
                cls.remove_scheduler_job(job_id=str(item.job_id))
                # 重新添加任务到调度器，确保配置是最新的
                cls.add_scheduler_job(item)
        
        # 添加事件监听器，监听所有调度器事件
        # EVENT_ALL表示监听所有类型的事件，包括任务开始、完成、异常等
        scheduler.add_listener(cls.scheduler_event_listener, EVENT_ALL)
        
        # 记录初始化完成日志
        logger.info('系统初始定时任务加载成功')

    @classmethod
    async def close_system_scheduler(cls):
        """
        应用关闭时关闭定时任务
        
        这个方法在应用关闭时被调用，用于：
        1. 优雅地关闭所有正在运行的任务
        2. 释放调度器资源
        3. 确保没有任务在应用关闭后继续运行
        
        :return: 无返回值
        """
        # 关闭调度器，停止所有任务调度
        scheduler.shutdown()
        logger.info('关闭定时任务成功')

    @classmethod
    def get_scheduler_job(cls, job_id: Union[str, int]):
        """
        根据任务id获取任务对象
        
        这个方法用于查询调度器中是否存在指定ID的任务：
        1. 将job_id转换为字符串格式（APScheduler要求）
        2. 从调度器中查找对应的任务对象
        3. 返回任务对象或None
        
        :param job_id: 任务ID，支持字符串或整数类型
        :return: 任务对象，如果不存在则返回None
        """
        # 从调度器中获取指定ID的任务对象
        query_job = scheduler.get_job(job_id=str(job_id))
        return query_job

    @classmethod
    def add_scheduler_job(cls, job_info: JobModel):
        """
        根据输入的任务对象信息添加任务到调度器
        
        这个方法负责将数据库中的任务配置转换为APScheduler可执行的任务：
        1. 解析任务执行目标函数
        2. 根据任务类型选择合适的执行器
        3. 解析Cron表达式创建触发器
        4. 设置任务的各种属性（并发控制、失败策略等）
        5. 将任务添加到调度器
        
        :param job_info: 任务对象信息，包含任务的所有配置参数
        :return: 无返回值
        """
        # 通过eval解析任务执行目标，获取实际的函数对象
        job_func = eval(job_info.invoke_target)
        
        # 获取任务指定的执行器
        job_executor = job_info.job_executor
        
        # 如果任务函数是协程函数，强制使用默认执行器（AsyncIOExecutor）
        # 因为协程函数只能在异步执行器中运行
        if iscoroutinefunction(job_func):
            job_executor = 'default'
        
        # 将任务添加到调度器，配置各种参数
        scheduler.add_job(
            # 任务执行函数
            func=eval(job_info.invoke_target),
            # 使用自定义的Cron触发器解析cron表达式
            trigger=MyCronTrigger.from_crontab(job_info.cron_expression),
            # 任务的位置参数，从字符串转换为列表
            args=job_info.job_args.split(',') if job_info.job_args else None,
            # 任务的关键字参数，从JSON字符串转换为字典
            kwargs=json.loads(job_info.job_kwargs) if job_info.job_kwargs else None,
            # 任务唯一标识符
            id=str(job_info.job_id),
            # 任务名称，用于日志和监控
            name=job_info.job_name,
            # 错过执行时间的宽限时间
            # 如果策略是'3'（忽略），设置一个很大的值
            misfire_grace_time=1000000000000 if job_info.misfire_policy == '3' else None,
            # 是否合并错过的任务
            # 如果策略是'2'（合并），则启用合并
            coalesce=True if job_info.misfire_policy == '2' else False,
            # 最大并发实例数
            # 如果允许并发('0')，设置为3；否则限制为1
            max_instances=3 if job_info.concurrent == '0' else 1,
            # 任务存储组，决定任务存储在哪里
            jobstore=job_info.job_group,
            # 任务执行器，决定任务如何执行
            executor=job_executor,
        )

    @classmethod
    def execute_scheduler_job_once(cls, job_info: JobModel):
        """
        根据输入的任务对象执行一次任务
        
        这个方法用于立即执行一次任务，通常用于测试或手动触发：
        1. 解析任务执行目标函数
        2. 选择合适的执行器
        3. 创建立即执行的触发器
        4. 如果任务状态为启用，还会创建定时触发器
        5. 将任务添加到调度器执行一次
        
        :param job_info: 任务对象信息
        :return: 无返回值
        """
        # 解析任务执行函数
        job_func = eval(job_info.invoke_target)
        
        # 获取执行器配置
        job_executor = job_info.job_executor
        
        # 协程函数必须使用默认执行器
        if iscoroutinefunction(job_func):
            job_executor = 'default'
        
        # 创建立即执行的触发器
        job_trigger = DateTrigger()
        
        # 如果任务状态为启用('0')，创建组合触发器
        # 组合触发器包含立即执行和定时执行两种方式
        if job_info.status == '0':
            job_trigger = OrTrigger(triggers=[
                DateTrigger(),  # 立即执行
                MyCronTrigger.from_crontab(job_info.cron_expression)  # 定时执行
            ])
        
        # 添加任务到调度器，立即执行一次
        scheduler.add_job(
            func=eval(job_info.invoke_target),
            trigger=job_trigger,
            args=job_info.job_args.split(',') if job_info.job_args else None,
            kwargs=json.loads(job_info.job_kwargs) if job_info.job_kwargs else None,
            id=str(job_info.job_id),
            name=job_info.job_name,
            misfire_grace_time=1000000000000 if job_info.misfire_policy == '3' else None,
            coalesce=True if job_info.misfire_policy == '2' else False,
            max_instances=3 if job_info.concurrent == '0' else 1,
            jobstore=job_info.job_group,
            executor=job_executor,
        )

    @classmethod
    def remove_scheduler_job(cls, job_id: Union[str, int]):
        """
        根据任务id移除任务
        
        这个方法用于从调度器中移除指定的任务：
        1. 先查询任务是否存在
        2. 如果存在则从调度器中移除
        3. 确保不会因为移除不存在的任务而报错
        
        :param job_id: 任务ID，支持字符串或整数类型
        :return: 无返回值
        """
        # 先查询任务是否存在
        query_job = cls.get_scheduler_job(job_id=job_id)
        
        # 只有当任务存在时才进行移除操作
        if query_job:
            scheduler.remove_job(job_id=str(job_id))

    @classmethod
    def scheduler_event_listener(cls, event):
        """
        调度器事件监听器
        
        这个方法监听APScheduler的所有事件，用于：
        1. 监控任务执行状态
        2. 记录任务执行日志
        3. 捕获任务执行异常
        4. 将执行信息保存到数据库
        
        :param event: 调度器事件对象，包含事件的详细信息
        :return: 无返回值
        """
        # 获取事件类型名称，用于日志记录
        event_type = event.__class__.__name__
        
        # 初始化任务执行状态和异常信息
        status = '0'  # 默认成功状态
        exception_info = ''  # 默认无异常
        
        # 如果是任务执行事件且有异常，记录异常信息
        if event_type == 'JobExecutionEvent' and event.exception:
            exception_info = str(event.exception)
            status = '1'  # 设置为失败状态
        
        # 检查事件是否包含任务ID
        if hasattr(event, 'job_id'):
            job_id = event.job_id
            
            # 获取任务对象，用于提取任务信息
            query_job = cls.get_scheduler_job(job_id=job_id)
            
            if query_job:
                # 获取任务的内部状态信息
                query_job_info = query_job.__getstate__()
                
                # 提取任务的各种属性信息
                job_name = query_job_info.get('name')  # 任务名称
                job_group = query_job._jobstore_alias  # 任务存储组
                job_executor = query_job_info.get('executor')  # 任务执行器
                invoke_target = query_job_info.get('func')  # 调用目标函数
                job_args = ','.join(query_job_info.get('args'))  # 位置参数
                job_kwargs = json.dumps(query_job_info.get('kwargs'))  # 关键字参数
                job_trigger = str(query_job_info.get('trigger'))  # 任务触发器
                
                # 构造任务执行日志消息
                job_message = f"事件类型: {event_type}, 任务ID: {job_id}, 任务名称: {job_name}, 执行于{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                # 创建任务日志模型对象
                job_log = JobLogModel(
                    jobName=job_name,
                    jobGroup=job_group,
                    jobExecutor=job_executor,
                    invokeTarget=invoke_target,
                    jobArgs=job_args,
                    jobKwargs=job_kwargs,
                    jobTrigger=job_trigger,
                    jobMessage=job_message,
                    status=status,
                    exceptionInfo=exception_info,
                    createTime=datetime.now(),
                )
                
                # 创建数据库会话并保存日志
                session = SessionLocal()
                JobLogService.add_job_log_services(session, job_log)
                session.close()
