# 导入FastAPI框架核心组件
from fastapi import FastAPI
# 导入FastAPI的CORS中间件，用于处理跨域资源共享
from fastapi.middleware.cors import CORSMiddleware


def add_cors_middleware(app: FastAPI):
    """
    添加CORS（跨域资源共享）中间件到FastAPI应用
    
    这个中间件的主要作用是：
    1. 允许前端页面从不同域名访问后端API
    2. 解决浏览器的同源策略限制
    3. 支持前后端分离架构
    4. 控制哪些域名可以访问API
    
    工作原理：
    - 在HTTP响应中添加CORS相关的响应头
    - 处理预检请求（OPTIONS方法）
    - 根据配置决定是否允许跨域访问
    
    安全考虑：
    - 只允许指定的域名访问（allow_origins）
    - 控制允许的HTTP方法（allow_methods）
    - 控制允许的请求头（allow_headers）
    - 控制是否允许携带认证信息（allow_credentials）
    
    :param app: FastAPI应用实例，用于添加中间件
    :return: 无返回值，直接修改传入的app对象
    """
    # 定义允许跨域访问的前端页面URL列表
    # 这些域名可以访问后端API
    origins = [
        'http://localhost:80',      # 本地开发环境，端口80
        'http://127.0.0.1:80',     # 本地开发环境，IP地址形式
    ]
    
    # 添加CORS中间件到应用
    app.add_middleware(
        CORSMiddleware,
        # 允许的源域名列表，只有这些域名可以跨域访问
        allow_origins=origins,
        # 是否允许携带认证信息（cookies、authorization headers等）
        allow_credentials=True,
        # 允许的HTTP方法，'*'表示允许所有方法
        allow_methods=['*'],
        # 允许的请求头，'*'表示允许所有请求头
        allow_headers=['*'],
    )
