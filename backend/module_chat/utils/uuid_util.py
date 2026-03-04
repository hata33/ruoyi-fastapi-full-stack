"""
UUID工具函数

说明：
- 提供统一的UUID生成和验证功能
- 用于生成消息ID、会话ID等唯一标识符
"""

import uuid
from typing import str


def generate_uuid() -> str:
    """
    生成标准的UUID字符串

    :return: UUID字符串（格式：xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx）
    """
    return str(uuid.uuid4())


def is_valid_uuid(uuid_str: str) -> bool:
    """
    验证字符串是否为有效的UUID

    :param uuid_str: 待验证的UUID字符串
    :return: 是否有效
    """
    try:
        uuid.UUID(uuid_str)
        return True
    except (ValueError, AttributeError):
        return False


def generate_short_id() -> str:
    """
    生成短ID（UUID的前8位）

    注意：短ID有碰撞风险，仅用于显示或非关键场景

    :return: 短ID字符串
    """
    return str(uuid.uuid4())[:8]
