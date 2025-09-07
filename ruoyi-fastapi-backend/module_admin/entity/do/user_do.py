from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from config.database import Base


class SysUser(Base):
    """
    用户信息表 - 存储系统用户的核心信息。

    Attributes:
        user_id (Integer): 用户ID，主键，自增。
        dept_id (Integer): 部门ID，关联部门表，可为空。
        user_name (String): 用户账号，不可为空，长度30。
        nick_name (String): 用户昵称，不可为空，长度30。
        user_type (String): 用户类型，默认为'00'（系统用户）。
        email (String): 用户邮箱，默认为空字符串，长度50。
        phonenumber (String): 手机号码，默认为空字符串，长度11。
        sex (String): 用户性别，'0'男, '1'女, '2'未知，默认为'0'。
        avatar (String): 头像地址，默认为空字符串，长度100。
        password (String): 密码，默认为空字符串，长度100。
        status (String): 账号状态，'0'正常, '1'停用，默认为'0'。
        del_flag (String): 删除标志，'0'代表存在, '2'代表删除，默认为'0'。
        login_ip (String): 最后登录IP，默认为空字符串，长度128。
        login_date (DateTime): 最后登录时间。
        create_by (String): 创建者，默认为空字符串，长度64。
        create_time (DateTime): 创建时间，默认为当前时间。
        update_by (String): 更新者，默认为空字符串，长度64。
        update_time (DateTime): 更新时间，默认为当前时间。
        remark (String): 备注信息，可为空，长度500。
    """

    __tablename__ = 'sys_user'

    user_id = Column(Integer, primary_key=True, autoincrement=True, comment='用户ID')
    dept_id = Column(Integer, default=None, comment='部门ID')
    user_name = Column(String(30), nullable=False, comment='用户账号')
    nick_name = Column(String(30), nullable=False, comment='用户昵称')
    user_type = Column(String(2), default='00', comment='用户类型（00系统用户）')
    email = Column(String(50), default='', comment='用户邮箱')
    phonenumber = Column(String(11), default='', comment='手机号码')
    sex = Column(String(1), default='0', comment='用户性别（0男 1女 2未知）')
    avatar = Column(String(100), default='', comment='头像地址')
    password = Column(String(100), default='', comment='密码')
    status = Column(String(1), default='0', comment='帐号状态（0正常 1停用）')
    del_flag = Column(String(1), default='0', comment='删除标志（0代表存在 2代表删除）')
    login_ip = Column(String(128), default='', comment='最后登录IP')
    login_date = Column(DateTime, comment='最后登录时间')
    create_by = Column(String(64), default='', comment='创建者')
    # `default=datetime.now` 是一个 Python callable，每次实例创建时都会被调用，用于生成默认值。
    create_time = Column(DateTime, comment='创建时间', default=datetime.now())
    update_by = Column(String(64), default='', comment='更新者')
    # `default=datetime.now` - 同上，用于更新时间的默认值。
    update_time = Column(DateTime, comment='更新时间', default=datetime.now())
    remark = Column(String(500), default=None, comment='备注')


class SysUserRole(Base):
    """
    用户和角色关联表 - 实现用户与角色的多对多关系。

    Attributes:
        user_id (Integer): 用户ID，复合主键的一部分，外键关联 SysUser.user_id。
        role_id (Integer): 角色ID，复合主键的一部分，外键关联 SysRole.role_id。
    """

    __tablename__ = 'sys_user_role'

    # 复合主键的定义，确保 user_id 和 role_id 的组合是唯一的。
    user_id = Column(Integer, primary_key=True, nullable=False, comment='用户ID')
    role_id = Column(Integer, primary_key=True, nullable=False, comment='角色ID')


class SysUserPost(Base):
    """
    用户与岗位关联表 - 实现用户与岗位的多对多关系。

    Attributes:
        user_id (Integer): 用户ID，复合主键的一部分，外键关联 SysUser.user_id。
        post_id (Integer): 岗位ID，复合主键的一部分，外键关联 SysPost.post_id。
    """

    __tablename__ = 'sys_user_post'

    # 复合主键的定义，确保 user_id 和 post_id 的组合是唯一的。
    user_id = Column(Integer, primary_key=True, nullable=False, comment='用户ID')
    post_id = Column(Integer, primary_key=True, nullable=False, comment='岗位ID')