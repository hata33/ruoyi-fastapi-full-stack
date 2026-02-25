from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from config.database import Base


class SysTaskCategory(Base):
    """
    任务分类表
    """
    __tablename__ = 'biz_task_category'

    category_id = Column(Integer, primary_key=True, autoincrement=True, comment='分类ID')
    category_name = Column(String(50), nullable=False, comment='分类名称')
    user_id = Column(Integer, comment='用户ID')
    sort_order = Column(Integer, default=0, comment='排序顺序')
    create_by = Column(String(64), default='', comment='创建者')
    create_time = Column(DateTime, comment='创建时间', default=datetime.now())
    update_by = Column(String(64), default='', comment='更新者')
    update_time = Column(DateTime, comment='更新时间', default=datetime.now())
    remark = Column(String(500), comment='备注')
