# 导入uvicorn，这是一个ASGI服务器，用于运行FastAPI应用
import uvicorn
# 从server模块导入app实例和AppConfig配置类
# noqa: F401表示忽略未使用导入的flake8警告
from server import app, AppConfig  # noqa: F401


# Python的标准入口点检查，确保代码只在直接运行此文件时执行，而不是在导入时执行
if __name__ == '__main__':
    # 使用uvicorn启动FastAPI应用
    uvicorn.run(
        app='app:app',  # 应用路径，格式为"文件名:应用实例名"
        host=AppConfig.app_host,  # 服务器主机地址，从AppConfig配置中获取
        port=AppConfig.app_port,  # 服务器端口，从AppConfig配置中获取
        root_path=AppConfig.app_root_path,  # API的根路径前缀，从AppConfig配置中获取
        reload=AppConfig.app_reload,  # 是否启用热重载，开发环境通常设为True，从AppConfig配置中获取
    )

"""
我将为 app.py 文件添加详细的注释，解释其功能和语法内容。现在开始修改文件。
我已经为 app.py 文件添加了详细的注释。以下是对该文件功能和语法的解释：

### 文件功能解释

这个 app.py 文件是 RuoYi-Vue3-FastAPI 项目后端的入口文件，主要用于启动 FastAPI 应用服务器。它使用 uvicorn（一个 ASGI 服务器）来运行 FastAPI 应用。

### 主要组件解释

1. **导入部分**：
   - `uvicorn`：ASGI 服务器，用于部署 FastAPI 应用
   - `app`：从 server 模块导入的 FastAPI 应用实例
   - `AppConfig`：从 server 模块导入的配置类，包含应用的各种配置参数

2. **入口点检查**：
   - `if __name__ == '__main__':`：这是 Python 的标准入口点检查，确保代码只在直接运行此文件时执行，而不是在被其他模块导入时执行

3. **应用启动配置**：
   - `uvicorn.run()`：启动 ASGI 服务器的方法，接受多个参数来配置服务器行为
   - 参数说明：
     - `app='app:app'`：指定应用的路径，格式为"文件名:应用实例名"
     - `host`：服务器监听的主机地址
     - `port`：服务器监听的端口号
     - `root_path`：API 的根路径前缀
     - `reload`：是否启用热重载功能（开发环境中通常设为 True）

### 语法特点

1. **注释标记**：
   - `# noqa: F401`：这是一个特殊的注释标记，告诉代码检查工具（如 flake8）忽略特定的警告，这里是忽略"导入但未使用"的警告

2. **配置参数获取**：
   - 使用 `AppConfig` 类的属性来获取配置参数，这是一种常见的配置管理模式，使配置集中化且易于维护

这个文件虽然简短，但它是整个 FastAPI 应用的启动点，通过配置类来灵活控制应用的运行参数，符合现代 Python Web 应用的最佳实践。
"""