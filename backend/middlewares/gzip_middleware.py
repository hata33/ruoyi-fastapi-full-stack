# 导入FastAPI框架核心组件
from fastapi import FastAPI, Response
from starlette.middleware.gzip import GZipMiddleware
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send


class NoGzipResponse:
    """包装响应，标记为不压缩"""

    def __init__(self, response: Response):
        self.response = response

    async def __call__(self, receive, send):
        await self.response(receive, send)


class CustomGZipMiddleware(GZipMiddleware):
    """
    自定义 Gzip 中间件，跳过 SSE 流式响应
    """

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        # 检查响应类型，如果是 SSE 则跳过压缩
        if scope["type"] == "http":
            # 检查请求路径是否为 SSE 端点
            path = scope.get("path", "")
            if "/stream" in path or "/regenerate" in path:
                # 直接传递，不压缩
                await self.app(scope, receive, send)
                return

        await super().__call__(scope, receive, send)


def add_gzip_middleware(app: FastAPI):
    """
    添加Gzip压缩中间件到FastAPI应用

    这个中间件的主要作用是：
    1. 自动压缩HTTP响应内容，减少网络传输数据量
    2. 提高页面加载速度，特别是对于文本内容（HTML、CSS、JS、JSON等）
    3. 减少带宽使用，提升用户体验
    4. 跳过 SSE 流式响应，避免破坏实时传输

    工作原理：
    - 检查客户端是否支持gzip压缩（Accept-Encoding头）
    - 对符合条件的响应内容进行gzip压缩
    - 添加Content-Encoding: gzip响应头
    - 只压缩大于minimum_size的响应
    - 跳过流式响应（/stream 和 /regenerate 端点）

    配置参数说明：
    - minimum_size: 最小压缩大小（字节），小于此值的响应不压缩
    - compresslevel: 压缩级别（1-9），9为最高压缩率但CPU消耗最大

    :param app: FastAPI应用实例，用于添加中间件
    :return: 无返回值，直接修改传入的app对象
    """
    # 使用自定义 Gzip 中间件，跳过 SSE 端点
    app.add_middleware(CustomGZipMiddleware, minimum_size=1000, compresslevel=9)
