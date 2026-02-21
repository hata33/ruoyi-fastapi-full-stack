# -*- coding: utf-8 -*-
"""
链路追踪上下文管理模块

@author: peng
@file: ctx.py
@time: 2025/1/17  16:57

该模块负责管理HTTP请求的上下文信息，特别是请求ID的生成和获取。
使用Python的contextvars模块实现请求级别的上下文隔离，确保在异步环境中
每个请求都有独立的上下文空间。
"""

# 导入Python标准库的上下文变量管理模块
import contextvars
# 导入UUID生成模块，用于生成唯一的请求标识符
from uuid import uuid4

# 定义全局的请求ID上下文变量
# 使用contextvars.ContextVar创建线程和异步任务安全的上下文变量
# 每个请求都会有自己的request-id值，互不干扰
CTX_REQUEST_ID: contextvars.ContextVar[str] = contextvars.ContextVar('request-id', default='')


class TraceCtx:
    """
    链路追踪上下文管理类
    
    该类提供了请求ID的生成和获取功能，确保在异步环境中
    每个请求都有唯一的标识符，支持分布式链路追踪。
    
    主要特性：
    - 线程安全：使用contextvars确保多线程环境下的安全性
    - 异步安全：支持asyncio异步环境下的上下文隔离
    - 请求隔离：每个请求都有独立的上下文空间
    - 自动生成：使用UUID4生成全局唯一的请求ID
    """
    
    @staticmethod
    def set_id():
        """
        生成并设置当前请求的ID
        
        该方法会：
        1. 生成一个新的UUID4字符串作为请求ID
        2. 将请求ID存储到当前请求的上下文中
        3. 返回生成的请求ID
        
        使用场景：
        - 在请求开始时调用，为请求分配唯一标识
        - 在中间件中自动调用，无需手动管理
        
        :return: 生成的请求ID字符串（32位十六进制）
        """
        # 生成新的UUID4并转换为十六进制字符串
        _id = uuid4().hex
        # 将请求ID存储到当前请求的上下文中
        CTX_REQUEST_ID.set(_id)
        return _id

    @staticmethod
    def get_id():
        """
        获取当前请求的ID
        
        该方法会：
        1. 从当前请求的上下文中获取请求ID
        2. 如果上下文中没有ID，返回默认值（空字符串）
        
        使用场景：
        - 在日志记录时获取请求ID，关联同一请求的所有日志
        - 在错误处理时获取请求ID，便于问题追踪
        - 在响应头中添加请求ID，支持前端追踪
        
        :return: 当前请求的ID字符串，如果不存在则返回空字符串
        """
        # 从当前请求的上下文中获取请求ID
        return CTX_REQUEST_ID.get()
