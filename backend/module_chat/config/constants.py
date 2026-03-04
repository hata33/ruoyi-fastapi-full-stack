"""
聊天模块常量定义

说明：
- 定义聊天模块使用的所有常量
- 包括用户ID类型、消息限制、配置参数等
"""

# ==================== 用户ID常量 ====================

class UserIds:
    """用户ID常量"""
    AI = 0  # AI消息的user_id
    SYSTEM = -1  # 系统消息的user_id


# ==================== 消息上下文配置 ====================

class MessageContext:
    """消息上下文配置"""
    MAX_RECENT_MESSAGES = 50  # 获取最近N条消息用于构建上下文
    MIN_MESSAGES_FOR_CONTEXT = 1  # 最少消息数


# ==================== 会话配置 ====================

class ConversationConfig:
    """会话配置"""
    DEFAULT_TITLE = '新对话'  # 默认会话标题
    MAX_TITLE_LENGTH = 50  # 会话标题最大长度
    TITLE_PREVIEW_LENGTH = 20  # 标题预览长度（首条消息前N字符）


# ==================== Token配置 ====================

class TokenConfig:
    """Token配置"""
    WARNING_THRESHOLD = 0.8  # Token使用警告阈值（80%）
    CRITICAL_THRESHOLD = 0.9  # Token使用严重阈值（90%）


# ==================== 模型配置 ====================

class ModelConfig:
    """模型配置"""
    DEFAULT_MODEL = 'deepseek-chat'  # 默认模型
    REASONER_MODEL = 'deepseek-reasoner'  # 推理模型

    # 允许的模型列表
    ALLOWED_MODELS = [
        'deepseek-chat',
        'deepseek-reasoner',
    ]


# ==================== SSE事件类型 ====================

class SSEEventType:
    """SSE事件类型"""
    MESSAGE_START = 'message_start'
    THINKING_START = 'thinking_start'
    THINKING_DELTA = 'thinking_delta'
    THINKING_END = 'thinking_end'
    CONTENT_DELTA = 'content_delta'
    MESSAGE_END = 'message_end'
    ERROR = 'error'


# ==================== 消息角色 ====================

class MessageRole:
    """消息角色"""
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'


# ==================== 附件配置 ====================

class AttachmentConfig:
    """附件配置"""
    MAX_ATTACHMENTS_PER_MESSAGE = 10  # 单条消息最大附件数
    ALLOWED_FILE_TYPES = [  # 允许的文件类型
        'image/jpeg',
        'image/png',
        'image/gif',
        'application/pdf',
        'text/plain',
    ]
    MAX_FILE_SIZE_MB = 10  # 最大文件大小（MB）


# ==================== API错误码 ====================

class ChatErrorCode:
    """聊天模块错误码"""
    CONVERSATION_NOT_FOUND = 2001
    MESSAGE_NOT_FOUND = 2002
    MODEL_DISABLED = 2003
    MODEL_NOT_FOUND = 2004
    PERMISSION_DENIED = 2005
    STREAM_GENERATION_FAILED = 2006
    INVALID_ATTACHMENT = 2007
