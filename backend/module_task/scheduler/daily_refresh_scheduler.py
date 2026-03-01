"""
每日任务刷新调度器

每日 00:00 自动执行，将所有 task_type='daily' 且 status='completed' 的任务重置为 'pending'
保留 completion_count 统计（不重置），忽略 status='disabled' 的任务
"""

from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from apscheduler.triggers.cron import CronTrigger
from config.database import AsyncSessionLocal
from module_task.entity.do.daily_task_do import DailyTaskDO
from utils.log_util import logger


async def refresh_daily_tasks():
    """
    每日刷新任务

    每日 00:00 自动执行，完成以下操作：
    1. 查找所有 task_type='daily' 且 status='completed' 的任务
    2. 将这些任务的状态重置为 'pending'
    3. 保留 completion_count 统计（不重置）
    4. 忽略 status='disabled' 的任务（不参与刷新）
    5. 记录操作日志

    Returns:
        dict: 包含刷新结果的字典，包括影响的行数和详细信息
    """
    start_time = datetime.now()
    logger.info('开始执行每日任务刷新调度器')

    try:
        async with AsyncSessionLocal() as session:
            # 构建查询条件：
            # - task_type = 'daily' (每日任务)
            # - status = 'completed' (已完成)
            # 注意：不需要显式排除 status='disabled'，因为条件 status='completed' 已经排除了 disabled 状态
            query = (
                select(DailyTaskDO)
                .where(
                    DailyTaskDO.task_type == 'daily',
                    DailyTaskDO.status == 'completed'
                )
            )

            # 执行查询获取需要刷新的任务列表
            result = await session.execute(query)
            tasks_to_refresh = result.scalars().all()

            # 记录找到的任务数量
            task_count = len(tasks_to_refresh)

            if task_count == 0:
                logger.info('没有需要刷新的每日任务')
                return {
                    'success': True,
                    'message': '没有需要刷新的每日任务',
                    'affected_rows': 0,
                    'execution_time': (datetime.now() - start_time).total_seconds()
                }

            # 记录任务详情（仅记录前10个任务，避免日志过长）
            task_details = [
                f"Task ID: {task.task_id}, Title: {task.title}, User ID: {task.user_id}"
                for task in tasks_to_refresh[:10]
            ]
            if task_count > 10:
                task_details.append(f"... 还有 {task_count - 10} 个任务")

            logger.info(f'找到 {task_count} 个需要刷新的每日任务')
            logger.debug(f'任务详情: {", ".join(task_details)}')

            # 批量更新任务状态为 'pending'
            # 保留 completion_count 和其他字段不变
            update_stmt = (
                update(DailyTaskDO)
                .where(
                    DailyTaskDO.task_type == 'daily',
                    DailyTaskDO.status == 'completed'
                )
                .values(
                    status='pending',
                    update_time=datetime.now()
                )
            )

            # 执行更新
            update_result = await session.execute(update_stmt)
            affected_rows = update_result.rowcount

            # 提交事务
            await session.commit()

            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()

            # 记录成功日志
            logger.info(f'每日任务刷新成功，共刷新 {affected_rows} 个任务，耗时 {execution_time:.2f} 秒')

            return {
                'success': True,
                'message': f'成功刷新 {affected_rows} 个每日任务',
                'affected_rows': affected_rows,
                'execution_time': execution_time,
                'tasks_refreshed': task_count
            }

    except Exception as e:
        # 记录错误日志
        logger.error(f'每日任务刷新失败: {str(e)}')

        # 计算执行时间
        execution_time = (datetime.now() - start_time).total_seconds()

        # 返回错误信息
        return {
            'success': False,
            'message': f'每日任务刷新失败: {str(e)}',
            'affected_rows': 0,
            'execution_time': execution_time,
            'error': str(e)
        }


def register_daily_refresh_scheduler():
    """
    注册每日刷新调度器

    将每日任务刷新任务注册到 APScheduler 中：
    - 使用 CronTrigger 设置每日 00:00 执行
    - 任务ID为 'daily_task_refresh'
    - 任务名称为 '每日任务刷新'

    该函数应在应用启动时被调用，通常在 config/get_scheduler.py 的 init_system_scheduler 方法中调用
    """
    # 延迟导入，避免循环依赖
    from config.get_scheduler import scheduler

    try:
        # 检查调度器是否已经启动
        if not scheduler.running:
            logger.warning('调度器未启动，无法注册每日刷新任务')
            return False

        # 检查任务是否已经存在
        existing_job = scheduler.get_job('daily_task_refresh')
        if existing_job:
            logger.info('每日任务刷新调度器已存在，跳过注册')
            return True

        # 添加定时任务
        # hour=0, minute=0 表示每天 00:00 执行
        scheduler.add_job(
            func=refresh_daily_tasks,  # 要执行的异步函数
            trigger=CronTrigger(hour=0, minute=0),  # 每日 00:00 触发
            id='daily_task_refresh',  # 任务唯一标识
            name='每日任务刷新',  # 任务名称
            misfire_grace_time=3600,  # 错过执行的宽限时间（1小时）
            coalesce=True,  # 合并错过的执行
            max_instances=1,  # 最大并发实例数为1，避免重复执行
            replace_existing=True,  # 如果任务已存在则替换
        )

        logger.info('每日任务刷新调度器注册成功')
        return True

    except Exception as e:
        logger.error(f'注册每日任务刷新调度器失败: {str(e)}')
        return False


def unregister_daily_refresh_scheduler():
    """
    注销每日刷新调度器

    从 APScheduler 中移除每日任务刷新任务

    Returns:
        bool: 注销是否成功
    """
    # 延迟导入，避免循环依赖
    from config.get_scheduler import scheduler

    try:
        # 检查任务是否存在
        existing_job = scheduler.get_job('daily_task_refresh')
        if not existing_job:
            logger.info('每日任务刷新调度器不存在，无需注销')
            return True

        # 移除任务
        scheduler.remove_job('daily_task_refresh')
        logger.info('每日任务刷新调度器注销成功')
        return True

    except Exception as e:
        logger.error(f'注销每日任务刷新调度器失败: {str(e)}')
        return False


# 导出函数和调度器注册函数
__all__ = [
    'refresh_daily_tasks',
    'register_daily_refresh_scheduler',
    'unregister_daily_refresh_scheduler',
]
