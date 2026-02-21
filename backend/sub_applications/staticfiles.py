# 导入FastAPI框架核心组件
from fastapi import FastAPI
# 导入FastAPI的静态文件服务组件，用于提供静态文件访问
from fastapi.staticfiles import StaticFiles
# 导入上传配置，包含上传路径和URL前缀等配置信息
from config.env import UploadConfig


def mount_staticfiles(app: FastAPI):
    """
    挂载静态文件到FastAPI应用
    
    这个函数的主要作用是：
    1. 将本地文件系统中的静态文件目录挂载到Web应用的URL路径上
    2. 使静态文件（如图片、文档、上传的文件等）可以通过HTTP请求访问
    3. 提供文件下载和预览功能
    
    挂载后的访问方式：
    - 本地文件路径：{UploadConfig.UPLOAD_PATH}
    - 访问URL：http://domain/{UploadConfig.UPLOAD_PREFIX}/filename
    
    :param app: FastAPI应用实例，用于挂载静态文件服务
    :return: 无返回值，直接修改传入的app对象
    """
    # 使用app.mount()方法挂载静态文件目录
    # 第一个参数：URL路径前缀，用户访问静态文件时使用的URL路径
    # 第二个参数：StaticFiles对象，指定要服务的本地目录
    # 第三个参数：挂载点的名称，用于标识这个挂载点
    app.mount(
        f'{UploadConfig.UPLOAD_PREFIX}',  # URL路径前缀，如 '/uploads' 或 '/static'
        StaticFiles(directory=f'{UploadConfig.UPLOAD_PATH}'),  # 本地文件目录路径
        name='profile'  # 挂载点名称，这里命名为'profile'表示用户资料相关文件
    )
