from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from config.database import Base


class SysNote(Base):
    """
    记事表
    """
    __tablename__ = 'biz_note'

    note_id = Column(Integer, primary_key=True, autoincrement=True, comment='记事ID')
    note_title = Column(String(200), nullable=False, comment='记事标题')
    note_content = Column(Text, comment='记事内容')
    category_id = Column(Integer, comment='分类ID')
    user_id = Column(Integer, comment='用户ID')
    status = Column(String(1), default='0', comment='状态（0正常 1关闭）')
    create_by = Column(String(64), default='', comment='创建者')
    create_time = Column(DateTime, comment='创建时间', default=datetime.now())
    update_by = Column(String(64), default='', comment='更新者')
    update_time = Column(DateTime, comment='更新时间', default=datetime.now())
    remark = Column(String(500), comment='备注')
