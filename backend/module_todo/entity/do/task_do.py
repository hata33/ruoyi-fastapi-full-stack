from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from config.database import Base


class SysTask(Base):
    """
    任务表
    """
    __tablename__ = 'biz_task'

    task_id = Column(Integer, primary_key=True, autoincrement=True, comment='任务ID')
    task_title = Column(String(200), nullable=False, comment='任务标题')
    task_content = Column(Text, comment='任务内容')
    category_id = Column(Integer, comment='分类ID')
    user_id = Column(Integer, comment='用户ID')
    task_type = Column(String(1), default='1', comment='任务类型（1任务 2待办）')
    status = Column(String(1), default='0', comment='状态（0待办 1已完成）')
    priority = Column(String(1), default='1', comment='优先级（0低 1中 2高）')
    due_date = Column(DateTime, comment='截止日期')
    completed_at = Column(DateTime, comment='完成时间')
    create_by = Column(String(64), default='', comment='创建者')
    create_time = Column(DateTime, comment='创建时间', default=datetime.now())
    update_by = Column(String(64), default='', comment='更新者')
    update_time = Column(DateTime, comment='更新时间', default=datetime.now())
    remark = Column(String(500), comment='备注')
