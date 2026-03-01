"""
每日任务刷新调度器测试脚本

用于手动测试每日任务刷新功能
"""

import asyncio
from datetime import datetime
from module_task.scheduler.daily_refresh_scheduler import refresh_daily_tasks


async def test_refresh():
    """
    测试每日任务刷新功能
    """
    print(f'开始测试每日任务刷新 - {datetime.now()}')
    print('=' * 60)

    # 执行刷新
    result = await refresh_daily_tasks()

    # 打印结果
    print('=' * 60)
    print(f'刷新结果: {result}')
    print('=' * 60)

    if result['success']:
        print(f"✓ 成功: {result['message']}")
        print(f"✓ 影响行数: {result['affected_rows']}")
        print(f"✓ 执行时间: {result['execution_time']:.2f} 秒")
    else:
        print(f"✗ 失败: {result['message']}")
        if 'error' in result:
            print(f"✗ 错误信息: {result['error']}")


if __name__ == '__main__':
    # 运行测试
    asyncio.run(test_refresh())
