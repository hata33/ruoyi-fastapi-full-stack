/**
 * Chat Module Type Definitions
 * 聊天模块类型定义
 */

// ==================== 基础类型 ====================

/** 消息角色 */
export type MessageRole = 'user' | 'assistant' | 'system';

/** 模型类型 */
export type ModelType = 'chat' | 'reasoner';

/** 主题模式 */
export type ThemeMode = 'light' | 'dark' | 'system';

/** 预设名称 */
export type PresetName = 'creative' | 'balanced' | 'precise';

/** 文件类型 */
export type FileType = 'pdf' | 'docx' | 'xlsx' | 'pptx' | 'image' | 'txt';

// ==================== 模型相关 ====================

/** AI 模型 */
export interface Model {
  modelId: number;
  modelCode: string;
  modelName: string;
  modelType: ModelType;
  maxTokens: number;
  isEnabled: boolean;
  sortOrder: number;
}

/** 用户模型配置 */
export interface ModelConfig {
  modelId: string;
  temperature: number;
  topP: number;
  maxTokens: number;
  presetName?: PresetName;
}

/** 模型预设 */
export interface ModelPreset {
  presetName: PresetName;
  displayName: string;
  description: string;
  temperature: number;
  topP: number;
}

// ==================== 标签相关 ====================

/** 会话标签 */
export interface Tag {
  tagId: number;
  tagName: string;
  tagColor: string;
  count?: number;
}

// ==================== 会话相关 ====================

/** 会话 */
export interface Conversation {
  conversationId: number;
  title: string;
  modelId: string;
  isPinned: boolean;
  pinTime?: string;
  tagList: string[];
  totalTokens: number;
  messageCount: number;
  createTime: string;
  updateTime: string;
}

/** 创建会话请求 */
export interface CreateConversationRequest {
  modelId?: string;
  title?: string;
  tagList?: string[];
}

/** 更新会话请求 */
export interface UpdateConversationRequest {
  conversationId: number;
  title?: string;
  modelId?: string;
  tagList?: string[];
}

/** 会话详情 */
export interface ConversationDetail extends Conversation {
  messages: Message[];
}

// ==================== 消息相关 ====================

/** 消息附件 */
export interface Attachment {
  fileId: number;
  fileName: string;
  fileType: FileType;
  fileSize: number;
  filePath: string;
}

/** 消息 */
export interface Message {
  messageId: number;
  conversationId: number;
  role: MessageRole;
  content: string;
  thinkingContent?: string;
  tokensUsed?: number;
  attachments: Attachment[];
  userId: number;
  createTime: string;
  isStreaming?: boolean;
  hasError?: boolean;
}

/** 发送消息请求 */
export interface SendMessageRequest {
  conversationId: number;
  content: string;
  modelId?: string;
  enableSearch?: boolean;
  attachments?: Array<{ fileId: number }>;
  temperature?: number;
  maxTokens?: number;
}

/** SSE 事件类型 */
export type SSEEventType =
  | 'message_start'
  | 'content_delta'
  | 'thinking_start'
  | 'thinking_delta'
  | 'thinking_end'
  | 'message_end'
  | 'error';

/** SSE 事件数据 */
export interface SSEEvent {
  type: SSEEventType;
  data: any;
}

// ==================== 文件相关 ====================

/** 文件信息 */
export interface ChatFile {
  fileId: number;
  fileName: string;
  filePath: string;
  fileType: FileType;
  fileSize: number;
  conversationId?: number;
  messageId?: number;
  userId: number;
  createTime: string;
}

// ==================== 用户设置 ====================

/** 用户设置 */
export interface UserSettings {
  themeMode: ThemeMode;
  defaultModel?: string;
  enableSearch?: boolean;
  streamOutput: boolean;
  fontSize?: number;
  language?: string;
}

// ==================== API 响应 ====================

/** API 响应基础结构 */
export interface ApiResponse<T = any> {
  code: number;
  msg: string;
  data: T;
}

/** 分页响应 */
export interface PaginatedResponse<T> {
  rows: T[];
  total: number;
}

/** 上下文状态 */
export interface ContextStatus {
  totalTokens: number;
  maxTokens: number;
  usagePercent: number;
  messageCount: number;
  warningLevel: 'normal' | 'warning' | 'critical';
}

// ==================== UI 状态 ====================

/** Toast 通知 */
export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
}

/** 加载状态 */
export interface LoadingState {
  loading: boolean;
  error?: string | null;
}
