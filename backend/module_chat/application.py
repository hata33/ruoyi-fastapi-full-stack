"""
聊天模块应用配置

说明：
- 配置聊天模块的路由注册
- 定义模块的配置类
"""

from fastapi import FastAPI


class ChatModuleConfig:
    """
    聊天模块配置类
    """

    def __init__(self, app: FastAPI):
        """
        初始化配置，注册路由

        :param app: FastAPI应用实例
        """
        self.app = app
        self._register_routers()

    def _register_routers(self):
        """
        注册聊天模块的所有路由
        """
        from module_chat.controller.chat_model_controller import chatModelController
        from module_chat.controller.chat_conversation_controller import chatConversationController, chatTagController
        from module_chat.controller.chat_message_controller import chatMessageController
        from module_chat.controller.chat_file_controller import chatFileController
        from module_chat.controller.chat_setting_controller import chatSettingController

        # 注册模型管理路由
        self.app.include_router(chatModelController, tags=['聊天-模型管理'])

        # 注册会话管理路由
        self.app.include_router(chatConversationController, tags=['聊天-会话管理'])

        # 注册标签管理路由
        self.app.include_router(chatTagController, tags=['聊天-标签管理'])

        # 注册消息管理路由
        self.app.include_router(chatMessageController, tags=['聊天-消息管理'])

        # 注册文件上传路由
        self.app.include_router(chatFileController, tags=['聊天-文件管理'])

        # 注册用户设置路由
        self.app.include_router(chatSettingController, tags=['聊天-用户设置'])
