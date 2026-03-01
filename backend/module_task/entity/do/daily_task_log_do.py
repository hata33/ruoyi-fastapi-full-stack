from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Index
from config.database import Base


class DailyTaskLogDO(Base):
    """
    每日任务日志表
    记录任务的各项操作日志，用于统计和追溯
    """
    __tablename__ = 'biz_daily_task_log'

    log_id = Column(Integer, primary_key=True, autoincrement=True, comment='日志ID')
    task_id = Column(Integer, nullable=False, comment='任务ID')
    user_id = Column(Integer, nullable=False, comment='用户ID')
    action_type = Column(String(20), nullable=False, comment='操作类型（create完成 reopen重开 disable禁用 enable启用 pin置顶 unpin取消置顶 reorder排序）')
    action_time = Column(DateTime, comment='操作时间', default=datetime.now())

    __table_args__ = (
        Index('idx_task_time', 'task_id', 'action_time'),
        Index('idx_user_time', 'user_id', 'action_time'),
    )
