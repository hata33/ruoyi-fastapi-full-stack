-- =============================================
-- AI聊天应用数据表初始化脚本
-- 版本: 1.0.0
-- 说明: 创建聊天模块所需的7张数据表
-- =============================================

-- ----------------------------
-- 1. 聊天会话表
-- ----------------------------
DROP TABLE IF EXISTS `chat_conversation`;
CREATE TABLE `chat_conversation` (
    `conversation_id` INT(11) NOT NULL AUTO_INCREMENT COMMENT '会话ID',
    `title` VARCHAR(200) NOT NULL DEFAULT '新对话' COMMENT '会话标题',
    `model_id` VARCHAR(50) NOT NULL COMMENT '当前使用的模型ID',
    `is_pinned` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否置顶',
    `pin_time` DATETIME DEFAULT NULL COMMENT '置顶时间',
    `tag_list` TEXT COMMENT '标签列表（JSON数组）',
    `total_tokens` INT(11) NOT NULL DEFAULT 0 COMMENT '会话累计使用的token数',
    `message_count` INT(11) NOT NULL DEFAULT 0 COMMENT '消息数量',
    `user_id` INT(11) NOT NULL COMMENT '所属用户ID',
    `create_by` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '创建者',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_by` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '更新者',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    PRIMARY KEY (`conversation_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_model_id` (`model_id`),
    KEY `idx_is_pinned` (`is_pinned`),
    KEY `idx_update_time` (`update_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聊天会话表';

-- ----------------------------
-- 2. 聊天消息表
-- ----------------------------
DROP TABLE IF EXISTS `chat_message`;
CREATE TABLE `chat_message` (
    `message_id` INT(11) NOT NULL AUTO_INCREMENT COMMENT '消息ID',
    `conversation_id` INT(11) NOT NULL COMMENT '所属会话ID',
    `role` VARCHAR(20) NOT NULL COMMENT '角色（user/assistant/system）',
    `content` TEXT NOT NULL COMMENT '消息内容',
    `thinking_content` TEXT COMMENT '推理过程内容（reasoner模型）',
    `tokens_used` INT(11) DEFAULT NULL COMMENT '本次消息使用的token数',
    `attachments` TEXT COMMENT '附件列表（JSON数组）',
    `user_id` INT(11) NOT NULL COMMENT '所属用户ID',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`message_id`),
    KEY `idx_conversation_id` (`conversation_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聊天消息表';

-- ----------------------------
-- 3. 聊天模型配置表
-- ----------------------------
DROP TABLE IF EXISTS `chat_model`;
CREATE TABLE `chat_model` (
    `model_id` INT(11) NOT NULL AUTO_INCREMENT COMMENT '模型ID',
    `model_code` VARCHAR(50) NOT NULL COMMENT '模型代码（如 deepseek-chat）',
    `model_name` VARCHAR(100) NOT NULL COMMENT '模型名称',
    `model_type` VARCHAR(20) NOT NULL COMMENT '模型类型（chat/reasoner）',
    `max_tokens` INT(11) NOT NULL COMMENT '最大token数',
    `is_enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    `sort_order` INT(11) NOT NULL DEFAULT 0 COMMENT '排序顺序',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`model_id`),
    UNIQUE KEY `uk_model_code` (`model_code`),
    KEY `idx_is_enabled` (`is_enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聊天模型配置表';

-- ----------------------------
-- 4. 用户模型配置表
-- ----------------------------
DROP TABLE IF EXISTS `chat_user_model_config`;
CREATE TABLE `chat_user_model_config` (
    `config_id` INT(11) NOT NULL AUTO_INCREMENT COMMENT '配置ID',
    `user_id` INT(11) NOT NULL COMMENT '用户ID',
    `model_id` VARCHAR(50) NOT NULL COMMENT '模型ID',
    `temperature` DECIMAL(3,2) DEFAULT NULL COMMENT '温度参数（0-2）',
    `top_p` DECIMAL(3,2) DEFAULT NULL COMMENT '采样参数（0-1）',
    `max_tokens` INT(11) DEFAULT NULL COMMENT '最大生成token数',
    `preset_name` VARCHAR(20) DEFAULT NULL COMMENT '预设名称（creative/balanced/precise）',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`config_id`),
    UNIQUE KEY `uk_user_model` (`user_id`, `model_id`),
    KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户模型配置表';

-- ----------------------------
-- 5. 聊天文件上传记录表
-- ----------------------------
DROP TABLE IF EXISTS `chat_file`;
CREATE TABLE `chat_file` (
    `file_id` INT(11) NOT NULL AUTO_INCREMENT COMMENT '文件ID',
    `file_name` VARCHAR(255) NOT NULL COMMENT '文件名',
    `file_path` VARCHAR(500) NOT NULL COMMENT '文件路径',
    `file_type` VARCHAR(20) NOT NULL COMMENT '文件类型（pdf/docx/xlsx/pptx/image）',
    `file_size` INT(11) NOT NULL COMMENT '文件大小（字节）',
    `conversation_id` INT(11) DEFAULT NULL COMMENT '关联会话ID',
    `message_id` INT(11) DEFAULT NULL COMMENT '关联消息ID',
    `user_id` INT(11) NOT NULL COMMENT '所属用户ID',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
    PRIMARY KEY (`file_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_conversation_id` (`conversation_id`),
    KEY `idx_message_id` (`message_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聊天文件上传记录表';

-- ----------------------------
-- 6. 会话标签表
-- ----------------------------
DROP TABLE IF EXISTS `chat_conversation_tag`;
CREATE TABLE `chat_conversation_tag` (
    `tag_id` INT(11) NOT NULL AUTO_INCREMENT COMMENT '标签ID',
    `tag_name` VARCHAR(20) NOT NULL COMMENT '标签名称',
    `tag_color` VARCHAR(20) DEFAULT NULL COMMENT '标签颜色',
    `user_id` INT(11) NOT NULL COMMENT '所属用户ID',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`tag_id`),
    KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会话标签表';

-- ----------------------------
-- 7. 用户设置表
-- ----------------------------
DROP TABLE IF EXISTS `chat_user_setting`;
CREATE TABLE `chat_user_setting` (
    `setting_id` INT(11) NOT NULL AUTO_INCREMENT COMMENT '设置ID',
    `user_id` INT(11) NOT NULL COMMENT '用户ID',
    `theme_mode` VARCHAR(10) NOT NULL DEFAULT 'system' COMMENT '主题模式（light/dark/system）',
    `default_model` VARCHAR(50) DEFAULT NULL COMMENT '默认模型',
    `enable_search` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否启用联网搜索',
    `stream_output` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用流式输出',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`setting_id`),
    UNIQUE KEY `uk_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户设置表';

-- ----------------------------
-- 初始化数据：插入示例模型配置
-- ----------------------------
INSERT INTO `chat_model` (`model_code`, `model_name`, `model_type`, `max_tokens`, `is_enabled`, `sort_order`) VALUES
('deepseek-chat', 'DeepSeek Chat', 'chat', 64000, 1, 1),
('deepseek-reasoner', 'DeepSeek Reasoner', 'reasoner', 64000, 1, 2);
