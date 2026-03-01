from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Index
from config.database import Base


class DailyTaskCategoryDO(Base):
    """
    每日任务分类表
    用于组织和管理不同类型的每日任务
    """
    __tablename__ = 'biz_daily_task_category'

    category_id = Column(Integer, primary_key=True, autoincrement=True, comment='分类ID')
    category_name = Column(String(50), nullable=False, comment='分类名称')
    category_icon = Column(String(50), comment='分类图标')
    sort_order = Column(Integer, default=0, comment='排序顺序（数值越小越靠前）')
    user_id = Column(Integer, nullable=False, comment='用户ID')
    create_by = Column(String(64), default='', comment='创建者')
    create_time = Column(DateTime, comment='创建时间', default=datetime.now())
    update_by = Column(String(64), default='', comment='更新者')
    update_time = Column(DateTime, comment='更新时间', default=datetime.now())
    remark = Column(String(500), comment='备注')

    __table_args__ = (
        Index('idx_category_user_sort', 'user_id', 'sort_order'),
    )
