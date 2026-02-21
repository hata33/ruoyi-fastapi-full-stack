# 导入FastAPI框架核心组件
from fastapi import FastAPI
# 导入链路追踪上下文管理类，用于管理请求ID
from .ctx import TraceCtx
# 导入链路追踪ASGI中间件，实现请求链路追踪功能
from .middle import TraceASGIMiddleware

# 定义模块的公共接口，只暴露这两个类
__all__ = ('TraceASGIMiddleware', 'TraceCtx')

# 模块版本号
__version__ = '0.1.0'


def add_trace_middleware(app: FastAPI):
    """
    添加链路追踪中间件到FastAPI应用
    
    这个中间件的主要作用是：
    1. 为每个HTTP请求生成唯一的请求ID（request-id）
    2. 在请求的整个生命周期中保持请求ID的一致性
    3. 在响应头中添加request-id，便于前端和日志系统追踪请求
    4. 支持分布式系统中的请求链路追踪
    
    工作原理：
    - 使用contextvars实现请求级别的上下文隔离
    - 在请求开始时生成UUID作为请求ID
    - 在响应头中添加X-Request-ID字段
    - 支持异步环境下的请求追踪
    
    使用场景：
    - 日志关联：通过request-id关联同一请求的所有日志
    - 错误追踪：快速定位问题请求的完整执行链路
    - 性能监控：分析请求的执行时间和资源消耗
    - 分布式追踪：在微服务架构中追踪请求流转
    
    :param app: FastAPI应用实例，用于添加中间件
    :return: 无返回值，直接修改传入的app对象
    """
    # 添加链路追踪中间件到应用
    # 该中间件会自动为每个请求生成唯一ID并添加到响应头中
    app.add_middleware(TraceASGIMiddleware)
