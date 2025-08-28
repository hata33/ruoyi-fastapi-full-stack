# -*- coding: utf-8 -*-
"""
链路追踪ASGI中间件模块

@author: peng
@file: middle.py
@time: 2025/1/17  16:57

该模块实现了ASGI标准的链路追踪中间件，用于在HTTP请求的生命周期中
注入请求ID，并支持请求和响应的拦截处理。
"""

# 导入函数装饰器工具，用于包装和增强函数功能
from functools import wraps
# 导入Starlette的ASGI类型定义，用于类型注解和接口实现
from starlette.types import ASGIApp, Message, Receive, Scope, Send
# 导入链路追踪的Span类和上下文管理器
from .span import get_current_span, Span


class TraceASGIMiddleware:
    """
    FastAPI链路追踪ASGI中间件
    
    该中间件实现了ASGI标准接口，用于：
    1. 拦截HTTP请求和响应
    2. 为每个请求创建追踪上下文
    3. 在响应头中添加请求ID
    4. 支持请求生命周期的监控
    
    使用方式：
    ```python
    app = FastAPI()
    app.add_middleware(TraceASGIMiddleware)
    ```
    
    工作原理：
    - 实现ASGI接口的__call__方法
    - 使用上下文管理器管理请求的生命周期
    - 包装receive和send函数以注入追踪逻辑
    - 只处理HTTP类型的请求，忽略其他类型
    """

    def __init__(self, app: ASGIApp) -> None:
        """
        初始化中间件
        
        :param app: 下一个ASGI应用或中间件
        """
        self.app = app

    @staticmethod
    async def my_receive(receive: Receive, span: Span):
        """
        包装receive函数，在请求接收前后注入追踪逻辑
        
        该方法会：
        1. 在接收请求前调用span.request_before()
        2. 包装原始的receive函数
        3. 在接收请求后调用span.request_after()
        
        :param receive: 原始的receive函数
        :param span: 当前请求的追踪上下文
        :return: 包装后的receive函数
        """
        # 在请求接收前执行，如设置请求ID、记录请求开始时间等
        await span.request_before()

        @wraps(receive)
        async def my_receive():
            """
            包装后的receive函数
            
            该函数会：
            1. 调用原始的receive函数获取消息
            2. 在消息接收后调用span.request_after()进行后处理
            3. 返回接收到的消息
            """
            # 调用原始的receive函数获取HTTP消息
            message = await receive()
            # 在请求接收后执行，如记录请求参数、解析请求体等
            await span.request_after(message)
            return message

        return my_receive

    # 第一步：__call__ 方法被调用
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        ASGI中间件的主要入口方法
        
        该方法实现了完整的请求处理流程：
        1. 检查请求类型，只处理HTTP请求
        2. 创建请求追踪上下文
        3. 包装receive和send函数
        4. 调用下一个ASGI应用
        
        :param scope: ASGI作用域，包含请求的元数据信息
        :param receive: 接收HTTP消息的函数
        :param send: 发送HTTP响应的函数
        :return: 无返回值
        """
        # 第二步：检查请求类型
        # 只处理HTTP类型的请求，忽略WebSocket等其他类型
        if scope['type'] != 'http':
            # 对于非HTTP请求，直接传递给下一个应用，不进行追踪
            await self.app(scope, receive, send)
            return

        # 第三步：创建追踪上下文
        # 使用异步上下文管理器创建和管理请求追踪上下文
        async with get_current_span(scope) as span:
            # 第四步：包装receive和send函数
            # 包装receive函数，注入请求追踪逻辑
            handle_outgoing_receive = await self.my_receive(receive, span)

            # 第五步：定义包装的 send 函数
            # 包装send函数，注入响应追踪逻辑
            async def handle_outgoing_request(message: 'Message') -> None:
                """
                包装后的send函数
                
                该函数会：
                1. 调用span.response()处理响应消息
                2. 调用原始的send函数发送响应
                """
                # 在发送响应前处理，如添加请求ID到响应头
                await span.response(message)
                # 调用原始的send函数发送响应
                await send(message)
            # 第六步：调用下一层应用（关键！）
            # 调用下一个ASGI应用，传入包装后的receive和send函数
            # 这样可以在请求处理的每个环节都注入追踪逻辑
            await self.app(scope, handle_outgoing_receive, handle_outgoing_request)
