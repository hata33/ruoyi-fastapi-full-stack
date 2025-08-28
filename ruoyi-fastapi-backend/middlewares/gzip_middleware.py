# 导入FastAPI框架核心组件
from fastapi import FastAPI
# 导入Starlette的Gzip压缩中间件，用于HTTP响应压缩
from starlette.middleware.gzip import GZipMiddleware


def add_gzip_middleware(app: FastAPI):
    """
    添加Gzip压缩中间件到FastAPI应用
    
    这个中间件的主要作用是：
    1. 自动压缩HTTP响应内容，减少网络传输数据量
    2. 提高页面加载速度，特别是对于文本内容（HTML、CSS、JS、JSON等）
    3. 减少带宽使用，提升用户体验
    
    工作原理：
    - 检查客户端是否支持gzip压缩（Accept-Encoding头）
    - 对符合条件的响应内容进行gzip压缩
    - 添加Content-Encoding: gzip响应头
    - 只压缩大于minimum_size的响应
    
    配置参数说明：
    - minimum_size: 最小压缩大小（字节），小于此值的响应不压缩
    - compresslevel: 压缩级别（1-9），9为最高压缩率但CPU消耗最大
    
    :param app: FastAPI应用实例，用于添加中间件
    :return: 无返回值，直接修改传入的app对象
    """
    # 添加Gzip压缩中间件到应用
    # minimum_size=1000: 只压缩大于1KB的响应，避免小响应压缩开销
    # compresslevel=9: 使用最高压缩级别，获得最佳压缩效果
    app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=9)
