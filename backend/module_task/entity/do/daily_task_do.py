from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text, Boolean, Enum, Index
from config.database import Base


class DailyTaskDO(Base):
    """
    每日任务表
    支持每日自动刷新、可勾选完成并自动置灰、自动累计完成次数、支持拖拽排序/置顶/置底、可设置禁用冻结的个人日常任务与习惯管理
    """
    __tablename__ = 'biz_daily_task'

    task_id = Column(Integer, primary_key=True, autoincrement=True, comment='任务ID')
    title = Column(String(200), nullable=False, comment='任务标题')
    description = Column(Text, comment='任务描述')
    task_type = Column(
        Enum('daily', 'once', 'long', name='daily_task_type'),
        default='daily',
        comment='任务类型（daily每日任务 once一次性任务 long长期任务）'
    )
    status = Column(
        Enum('pending', 'completed', 'disabled', name='daily_task_status'),
        default='pending',
        comment='任务状态（pending待完成 completed已完成 disabled已禁用）'
    )
    is_pinned = Column(Boolean, default=False, comment='是否置顶')
    sort_order = Column(Integer, default=0, comment='排序顺序（数值越小越靠前）')
    completion_count = Column(Integer, default=0, comment='累计完成次数')
    icon_type = Column(String(20), default='calendar', comment='图标类型')
    user_id = Column(Integer, nullable=False, comment='用户ID')
    category_id = Column(Integer, comment='分类ID')
    last_completed_at = Column(DateTime, comment='最后完成时间')
    disabled_at = Column(DateTime, comment='禁用时间')
    create_by = Column(String(64), default='', comment='创建者')
    create_time = Column(DateTime, comment='创建时间', default=datetime.now())
    update_by = Column(String(64), default='', comment='更新者')
    update_time = Column(DateTime, comment='更新时间', default=datetime.now())
    remark = Column(String(500), comment='备注')

    __table_args__ = (
        Index('idx_user_type', 'user_id', 'task_type'),
        Index('idx_user_sort', 'user_id', 'sort_order'),
        Index('idx_user_pinned', 'user_id', 'is_pinned', 'sort_order'),
    )
