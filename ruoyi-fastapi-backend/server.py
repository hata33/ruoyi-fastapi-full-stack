"""
我将为 server.py 文件添加详细的注释，解释其功能和语法内容。现在开始修改文件。
我已经为 server.py 文件添加了详细的注释。下面是对该文件功能和语法的简要总结：

## server.py 文件总结

### 文件功能概述

这个文件是 RuoYi-Vue3-FastAPI 项目的核心服务器配置文件，主要负责：

1. **FastAPI 应用初始化**：创建并配置 FastAPI 应用实例
2. **生命周期管理**：定义应用启动和关闭时的资源初始化与释放
3. **路由注册**：注册系统所有模块的 API 路由
4. **中间件与异常处理**：配置全局中间件和异常处理机制

### 主要组件解析

1. **导入部分**：
   - 导入 FastAPI 框架核心组件
   - 导入配置类和工具类
   - 导入各个功能模块的控制器
   - 导入中间件、异常处理和子应用处理函数

2. **生命周期管理**：
   - 使用 `@asynccontextmanager` 装饰器定义异步生命周期管理函数
   - 在应用启动时初始化数据库、Redis 连接池和调度器
   - 在应用关闭时释放资源

3. **应用初始化**：
   - 创建 FastAPI 实例并配置标题、描述和版本信息
   - 设置生命周期管理函数

4. **应用配置**：
   - 挂载子应用
   - 加载中间件处理方法
   - 配置全局异常处理

5. **路由注册**：
   - 定义控制器列表，包含各个功能模块的路由和标签
   - 通过循环将所有控制器注册到 FastAPI 应用

### 技术特点

1. **异步编程**：
   - 使用 `async/await` 语法进行异步操作
   - 通过异步上下文管理器管理资源生命周期

2. **模块化设计**：
   - 按功能模块组织控制器
   - 清晰的代码结构和职责划分

3. **依赖注入**：
   - 通过 FastAPI 的依赖注入系统管理组件依赖

4. **API 文档自动生成**：
   - 使用标签对 API 进行分组
   - 自动生成 Swagger/OpenAPI 文档

这个文件是整个后端应用的核心骨架，定义了应用的基本结构和启动流程，遵循了 FastAPI 的最佳实践和现代 Python Web 开发的设计模式
"""
# 导入异步上下文管理器，用于管理FastAPI应用的生命周期
from contextlib import asynccontextmanager
# 导入FastAPI框架核心类
from fastapi import FastAPI
# 导入应用配置类
from config.env import AppConfig
# 导入数据库初始化函数
from config.get_db import init_create_table
# 导入Redis工具类
from config.get_redis import RedisUtil
# 导入调度器工具类
from config.get_scheduler import SchedulerUtil
# 导入全局异常处理函数
from exceptions.handle import handle_exception
# 导入中间件处理函数
from middlewares.handle import handle_middleware

# 导入各个控制器模块 - 管理模块
from module_admin.controller.cache_controller import cacheController
from module_admin.controller.captcha_controller import captchaController
from module_admin.controller.common_controller import commonController
from module_admin.controller.config_controller import configController
from module_admin.controller.dept_controller import deptController
from module_admin.controller.dict_controller import dictController
from module_admin.controller.log_controller import logController
from module_admin.controller.login_controller import loginController
from module_admin.controller.job_controller import jobController
from module_admin.controller.menu_controller import menuController
from module_admin.controller.notice_controller import noticeController
from module_admin.controller.online_controller import onlineController
from module_admin.controller.post_controler import postController
from module_admin.controller.role_controller import roleController
from module_admin.controller.server_controller import serverController
from module_admin.controller.user_controller import userController

# 导入代码生成模块控制器
from module_generator.controller.gen_controller import genController
# 导入子应用处理函数
from sub_applications.handle import handle_sub_applications
# 导入通用工具函数
from utils.common_util import worship
# 导入日志工具
from utils.log_util import logger


# 定义应用生命周期事件处理函数
@asynccontextmanager  # 使用异步上下文管理器装饰器
async def lifespan(app: FastAPI):
    """
    FastAPI应用生命周期管理函数
    在应用启动时初始化资源，应用关闭时释放资源
    """
    # 记录应用启动日志
    logger.info(f'{AppConfig.app_name}开始启动')
    # 执行启动欢迎函数
    worship()
    # 初始化并创建数据库表
    await init_create_table()
    # 创建Redis连接池并存储在应用状态中，app.state.redis 确保整个应用只创建一个 Redis 连接池实例
    app.state.redis = await RedisUtil.create_redis_pool()
    # 初始化系统字典到Redis
    await RedisUtil.init_sys_dict(app.state.redis)
    # 初始化系统配置到Redis
    await RedisUtil.init_sys_config(app.state.redis)
    # 初始化系统调度器
    await SchedulerUtil.init_system_scheduler()
    # 记录应用启动成功日志
    logger.info(f'{AppConfig.app_name}启动成功')
    # yield语句分隔启动和关闭逻辑
    yield
    # 应用关闭时关闭Redis连接池
    await RedisUtil.close_redis_pool(app)
    # 应用关闭时关闭系统调度器
    await SchedulerUtil.close_system_scheduler()


# 初始化FastAPI应用实例
app = FastAPI(
    title=AppConfig.app_name,  # 设置API文档标题
    description=f'{AppConfig.app_name}接口文档',  # 设置API文档描述
    version=AppConfig.app_version,  # 设置API版本号
    lifespan=lifespan,  # 设置应用生命周期管理函数
)

# 挂载子应用到主应用
handle_sub_applications(app)  # 处理子应用的挂载逻辑
# 加载中间件处理方法，如认证、CORS等
handle_middleware(app)
# 加载全局异常处理方法，统一处理API异常
handle_exception(app)


# 定义系统所有路由控制器列表
controller_list = [
    # 基础功能模块
    {'router': loginController, 'tags': ['登录模块']},  # 用户登录相关API
    {'router': captchaController, 'tags': ['验证码模块']},  # 验证码生成与验证API
    
    # 系统管理模块
    {'router': userController, 'tags': ['系统管理-用户管理']},  # 用户CRUD操作API
    {'router': roleController, 'tags': ['系统管理-角色管理']},  # 角色权限管理API
    {'router': menuController, 'tags': ['系统管理-菜单管理']},  # 系统菜单管理API
    {'router': deptController, 'tags': ['系统管理-部门管理']},  # 部门组织结构管理API
    {'router': postController, 'tags': ['系统管理-岗位管理']},  # 岗位管理API
    {'router': dictController, 'tags': ['系统管理-字典管理']},  # 系统字典管理API
    {'router': configController, 'tags': ['系统管理-参数管理']},  # 系统参数配置API
    {'router': noticeController, 'tags': ['系统管理-通知公告管理']},  # 系统公告管理API
    {'router': logController, 'tags': ['系统管理-日志管理']},  # 系统日志查询API
    
    # 系统监控模块
    {'router': onlineController, 'tags': ['系统监控-在线用户']},  # 在线用户监控API
    {'router': jobController, 'tags': ['系统监控-定时任务']},  # 定时任务管理API
    {'router': serverController, 'tags': ['系统监控-菜单管理']},  # 服务器监控API
    {'router': cacheController, 'tags': ['系统监控-缓存监控']},  # 缓存监控API
    
    # 其他功能模块
    {'router': commonController, 'tags': ['通用模块']},  # 通用功能API
    {'router': genController, 'tags': ['代码生成']},  # 代码生成器API
]

# 遍历控制器列表，将每个控制器注册到FastAPI应用
for controller in controller_list:
    # 使用include_router方法注册路由，设置对应的标签用于API文档分组
    app.include_router(router=controller.get('router'), tags=controller.get('tags'))
