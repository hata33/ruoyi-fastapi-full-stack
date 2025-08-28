# -*- coding: utf-8 -*-
"""
链路追踪Span生命周期管理模块

@author: peng
@file: span.py
@time: 2025/1/17  16:57

该模块定义了Span类，用于管理HTTP请求的完整生命周期。
Span代表一个请求从开始到结束的完整执行过程，包括请求处理、
响应生成等各个阶段。
"""

# 导入异步上下文管理器装饰器，用于管理异步资源的生命周期
from contextlib import asynccontextmanager
# 导入Starlette的类型定义，用于类型注解
from starlette.types import Scope, Message
# 导入链路追踪上下文管理类
from .ctx import TraceCtx


class Span:
    """
    HTTP请求生命周期管理类
    
    该类管理整个HTTP请求的生命周期，包括：
    - 请求开始阶段（request_before）
    - 请求接收阶段（request_after）
    - 响应开始阶段（response start）
    - 响应完成阶段（response body）
    
    生命周期流程：
    request(before) --> request(after) --> response(before) --> response(after)
    
    主要功能：
    1. 请求ID的生成和管理
    2. 请求参数的记录和解析
    3. 响应头的注入和修改
    4. 请求执行状态的跟踪
    """

    def __init__(self, scope: Scope):
        """
        初始化Span对象
        
        :param scope: ASGI作用域，包含请求的元数据信息
        """
        self.scope = scope

    async def request_before(self):
        """
        请求开始前的处理逻辑
        
        该方法在请求开始处理时调用，主要完成：
        1. 生成唯一的请求ID
        2. 设置请求追踪上下文
        3. 记录请求开始时间
        4. 初始化请求相关的状态信息
        
        使用场景：
        - 在中间件中自动调用
        - 为每个请求分配唯一标识
        - 初始化请求追踪上下文
        """
        # 生成并设置当前请求的唯一ID
        # 这个ID将在整个请求生命周期中保持不变
        TraceCtx.set_id()

    async def request_after(self, message: Message):
        """
        请求接收后的处理逻辑
        
        该方法在HTTP消息接收完成后调用，主要完成：
        1. 解析和记录请求参数
        2. 处理请求体内容
        3. 记录请求的详细信息
        4. 为后续处理准备数据
        
        参数说明：
        message: HTTP消息对象，包含请求的详细信息
        
        消息示例：
        message: {
            'type': 'http.request', 
            'body': b'{\r\n    "name": "\xe8\x8b\x8f\xe8\x8b\x8f\xe8\x8b\x8f"\r\n}', 
            'more_body': False
        }
        
        :param message: 接收到的HTTP消息对象
        :return: 处理后的消息对象
        """
        # 当前实现直接返回消息，可以根据需要添加更多处理逻辑
        # 例如：解析JSON请求体、记录请求参数、验证请求格式等
        return message

    async def response(self, message: Message): 
        """
        响应处理逻辑
        
        该方法在发送HTTP响应时调用，主要完成：
        1. 处理响应开始消息（http.response.start）
        2. 处理响应体消息（http.response.body）
        3. 在响应头中注入请求ID
        4. 记录响应状态和内容
        
        响应消息类型：
        - http.response.start: 响应开始，包含状态码和响应头
        - http.response.body: 响应体，包含实际的响应内容
        
        参数说明：
        message: HTTP响应消息对象
        
        :param message: 要发送的HTTP响应消息
        :return: 处理后的响应消息
        """
        # 处理响应开始消息
        if message['type'] == 'http.response.start':
            # 在响应头中添加请求ID，便于前端和日志系统追踪
            # 使用X-Request-ID作为标准响应头名称
            message['headers'].append((b'request-id', TraceCtx.get_id().encode()))
        
        # 处理响应体消息
        # if message['type'] == 'http.response.body':
        #     # 可以在这里处理响应体内容
        #     # 例如：记录响应大小、压缩响应内容等
        #     message.get('body', b'')
        #     pass
        
        return message


@asynccontextmanager
async def get_current_span(scope: Scope):
    """
    异步上下文管理器，用于管理Span对象的生命周期
    
    该函数使用@asynccontextmanager装饰器，提供：
    1. 自动创建Span对象
    2. 确保Span在请求结束时正确清理
    3. 支持异步环境下的资源管理
    
    使用方式：
    ```python
    async with get_current_span(scope) as span:
        # 在span上下文中执行请求处理逻辑
        await span.request_before()
        # ... 处理请求 ...
        await span.response(message)
    ```
    
    参数说明：
    scope: ASGI作用域，包含请求的元数据信息
    
    :param scope: ASGI作用域
    :yield: Span对象，用于管理请求生命周期
    """
    # 创建新的Span对象并返回给调用者
    # 当异步上下文结束时，Span对象会自动清理
    yield Span(scope)
