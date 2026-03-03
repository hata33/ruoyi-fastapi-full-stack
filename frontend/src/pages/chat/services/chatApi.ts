/**
 * Chat Module API Service
 * 聊天模块 API 服务层
 */

import http from '@/common/utils/http';
import type { ApiResponse } from '@/common/utils/http';
import { streamRequest } from '@/common/utils/stream';
import type {
  PaginatedResponse,
  Model,
  ModelConfig,
  ModelPreset,
  Conversation,
  ConversationDetail,
  CreateConversationRequest,
  UpdateConversationRequest,
  Tag,
  Message,
  SendMessageRequest,
  ChatFile,
  UserSettings,
  ContextStatus,
  SSEEvent,
} from '../types';

// ==================== 模型管理 ====================

/**
 * 获取可用模型列表
 */
export const fetchModels = async (isEnabled?: boolean): Promise<ApiResponse<Model[]>> => {
  return http.get('/api/chat/models', {
    params: { isEnabled },
  });
};

/**
 * 获取用户模型配置
 */
export const fetchModelConfig = async (modelId?: string): Promise<ApiResponse<ModelConfig>> => {
  return http.get('/api/chat/model-config', {
    params: { modelId },
  });
};

/**
 * 保存用户模型配置
 */
export const saveModelConfig = async (config: ModelConfig): Promise<ApiResponse<{ msg: string }>> => {
  return http.post('/api/chat/model-config', config);
};

/**
 * 获取模型参数预设
 */
export const fetchModelPresets = async (): Promise<ApiResponse<ModelPreset[]>> => {
  return http.get('/api/chat/model-presets');
};

// ==================== 会话管理 ====================

/**
 * 获取会话列表（分页）
 */
export const fetchConversations = async (params?: {
  title?: string;
  modelId?: string;
  isPinned?: boolean;
  tagId?: number;
  beginTime?: string;
  endTime?: string;
  pageNum?: number;
  pageSize?: number;
}): Promise<ApiResponse<PaginatedResponse<Conversation>>> => {
  return http.get(
    '/api/chat/conversations',
    { params },
  );
};

/**
 * 获取会话详情
 */
export const fetchConversationDetail = async (conversationId: number): Promise<ApiResponse<ConversationDetail>> => {
  return http.get(
    `/api/chat/conversations/${conversationId}`,
  );
};

/**
 * 新建会话
 */
export const createConversation = async (data: CreateConversationRequest): Promise<ApiResponse<Conversation>> => {
  return http.post('/api/chat/conversations', data);
};

/**
 * 更新会话信息
 */
export const updateConversation = async (data: UpdateConversationRequest): Promise<ApiResponse<{ msg: string }>> => {
  return http.put('/api/chat/conversations', data);
};

/**
 * 删除会话
 */
export const deleteConversation = async (conversationIds: (number | string)[]): Promise<ApiResponse<{ msg: string }>> => {
  return http.delete(
    `/api/chat/conversations/${conversationIds.join(',')}`,
  );
};

/**
 * 置顶/取消置顶会话
 */
export const toggleConversationPin = async (
  conversationId: number,
  isPinned: boolean,
): Promise<ApiResponse<{ msg: string }>> => {
  return http.put(
    `/api/chat/conversations/${conversationId}/pin`,
    { isPinned },
  );
};

/**
 * 导出会话
 */
export const exportConversation = async (
  conversationId: number,
  format: 'markdown' | 'pdf' | 'txt',
): Promise<ApiResponse<{ downloadUrl: string; fileName: string; fileSize: number }>> => {
  return http.get(
    `/api/chat/conversations/${conversationId}/export`,
    { params: { format } },
  );
};

/**
 * 获取会话上下文状态
 */
export const fetchConversationContext = async (conversationId: number): Promise<ApiResponse<ContextStatus>> => {
  return http.get(
    `/api/chat/conversations/${conversationId}/context`,
  );
};

// ==================== 标签管理 ====================

/**
 * 获取标签列表
 */
export const fetchTags = async (): Promise<ApiResponse<Tag[]>> => {
  return http.get('/api/chat/tags');
};

/**
 * 创建标签
 */
export const createTag = async (tagName: string, tagColor?: string): Promise<ApiResponse<Tag>> => {
  return http.post('/api/chat/tags', { tagName, tagColor });
};

/**
 * 删除标签
 */
export const deleteTag = async (tagIds: (number | string)[]): Promise<ApiResponse<{ msg: string }>> => {
  return http.delete(`/api/chat/tags/${tagIds.join(',')}`);
};

// ==================== 消息管理 ====================

/**
 * 获取消息列表
 */
export const fetchMessages = async (
  conversationId: number,
  beforeMessageId?: number,
  pageSize = 50,
): Promise<ApiResponse<PaginatedResponse<Message> & { hasMore: boolean }>> => {
  return http.get(`/api/chat/conversations/${conversationId}/messages`, {
    params: { beforeMessageId, pageSize },
  });
};

/**
 * 发送消息（流式）
 *
 * @param data - 发送消息请求
 * @param onEvent - SSE 事件回调
 * @param onError - 错误回调
 * @param onComplete - 完成回调
 * @returns 取消请求的函数
 */
export const sendMessageStream = (
  data: SendMessageRequest,
  onEvent: (event: SSEEvent) => void,
  onError?: (error: Error) => void,
  onComplete?: () => void,
): (() => void) => {
  const baseURL = import.meta.env.DEV ? '/dev-api' : '/prod-api';
  const url = `${baseURL}/api/chat/messages/stream`;

  return streamRequest({
    url,
    method: 'POST',
    body: data,
    onEvent,
    onError,
    onComplete,
  });
};

/**
 * 停止生成消息
 */
export const stopMessageGeneration = async (messageId: number): Promise<ApiResponse<{ msg: string }>> => {
  return http.post(`/api/chat/messages/${messageId}/stop`);
};

/**
 * 重新生成消息（流式）
 *
 * @param messageId - 消息ID
 * @param modelId - 模型ID（可选）
 * @param onEvent - SSE 事件回调
 * @param onError - 错误回调
 * @param onComplete - 完成回调
 * @returns 取消请求的函数
 */
export const regenerateMessageStream = (
  messageId: number,
  modelId: string | undefined,
  onEvent: (event: SSEEvent) => void,
  onError?: (error: Error) => void,
  onComplete?: () => void,
): (() => void) => {
  const baseURL = import.meta.env.DEV ? '/dev-api' : '/prod-api';
  const url = `${baseURL}/api/chat/messages/${messageId}/regenerate`;

  return streamRequest({
    url,
    method: 'POST',
    body: modelId ? { modelId } : {},
    onEvent,
    onError,
    onComplete,
  });
};

// ==================== 文件管理 ====================

/**
 * 上传文件
 */
export const uploadFile = async (file: File, conversationId?: number): Promise<ApiResponse<ChatFile>> => {
  const formData = new FormData();
  formData.append('file', file);
  if (conversationId) {
    formData.append('conversationId', conversationId.toString());
  }

  return http.post('/api/chat/files/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

/**
 * 获取文件列表
 */
export const fetchFiles = async (params?: {
  fileType?: string;
  conversationId?: number;
  pageNum?: number;
  pageSize?: number;
}): Promise<ApiResponse<PaginatedResponse<ChatFile>>> => {
  return http.get('/api/chat/files', {
    params,
  });
};

/**
 * 删除文件
 */
export const deleteFile = async (fileIds: (number | string)[]): Promise<ApiResponse<{ msg: string }>> => {
  return http.delete(`/api/chat/files/${fileIds.join(',')}`);
};

// ==================== 用户设置 ====================

/**
 * 获取用户设置
 */
export const fetchUserSettings = async (): Promise<ApiResponse<UserSettings>> => {
  return http.get('/api/chat/settings');
};

/**
 * 更新用户设置
 */
export const updateUserSettings = async (settings: Partial<UserSettings>): Promise<ApiResponse<{ msg: string }>> => {
  return http.put('/api/chat/settings', settings);
};
