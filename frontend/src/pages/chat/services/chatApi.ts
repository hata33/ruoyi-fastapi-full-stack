/**
 * Chat Module API Service
 * 聊天模块 API 服务层
 */

import http from '@/common/utils/http';
import type {
  ApiResponse,
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
} from '../types';

// ==================== 模型管理 ====================

/**
 * 获取可用模型列表
 */
export const fetchModels = async (isEnabled?: boolean) => {
  return http.get<{ code: number; data: Model[] }>('/api/chat/models', {
    params: { isEnabled },
  });
};

/**
 * 获取用户模型配置
 */
export const fetchModelConfig = async (modelId?: string) => {
  return http.get<{ code: number; data: ModelConfig }>('/api/chat/model-config', {
    params: { modelId },
  });
};

/**
 * 保存用户模型配置
 */
export const saveModelConfig = async (config: ModelConfig) => {
  return http.post<{ code: number; msg: string }>('/api/chat/model-config', config);
};

/**
 * 获取模型参数预设
 */
export const fetchModelPresets = async () => {
  return http.get<{ code: number; data: ModelPreset[] }>('/api/chat/model-presets');
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
}) => {
  return http.get<{ code: number; data: PaginatedResponse<Conversation> }>(
    '/api/chat/conversations',
    { params },
  );
};

/**
 * 获取会话详情
 */
export const fetchConversationDetail = async (conversationId: number) => {
  return http.get<{ code: number; data: ConversationDetail }>(
    `/api/chat/conversations/${conversationId}`,
  );
};

/**
 * 新建会话
 */
export const createConversation = async (data: CreateConversationRequest) => {
  return http.post<{ code: number; data: Conversation }>('/api/chat/conversations', data);
};

/**
 * 更新会话信息
 */
export const updateConversation = async (data: UpdateConversationRequest) => {
  return http.put<{ code: number; msg: string }>('/api/chat/conversations', data);
};

/**
 * 删除会话
 */
export const deleteConversation = async (conversationIds: (number | string)[]) => {
  return http.delete<{ code: number; msg: string }>(
    `/api/chat/conversations/${conversationIds.join(',')}`,
  );
};

/**
 * 置顶/取消置顶会话
 */
export const toggleConversationPin = async (
  conversationId: number,
  isPinned: boolean,
) => {
  return http.put<{ code: number; msg: string }>(
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
) => {
  return http.get<{ code: number; data: { downloadUrl: string; fileName: string; fileSize: number } }>(
    `/api/chat/conversations/${conversationId}/export`,
    { params: { format } },
  );
};

/**
 * 获取会话上下文状态
 */
export const fetchConversationContext = async (conversationId: number) => {
  return http.get<{ code: number; data: ContextStatus }>(
    `/api/chat/conversations/${conversationId}/context`,
  );
};

// ==================== 标签管理 ====================

/**
 * 获取标签列表
 */
export const fetchTags = async () => {
  return http.get<{ code: number; data: Tag[] }>('/api/chat/tags');
};

/**
 * 创建标签
 */
export const createTag = async (tagName: string, tagColor?: string) => {
  return http.post<{ code: number; data: Tag }>('/api/chat/tags', { tagName, tagColor });
};

/**
 * 删除标签
 */
export const deleteTag = async (tagIds: (number | string)[]) => {
  return http.delete<{ code: number; msg: string }>(`/api/chat/tags/${tagIds.join(',')}`);
};

// ==================== 消息管理 ====================

/**
 * 获取消息列表
 */
export const fetchMessages = async (
  conversationId: number,
  beforeMessageId?: number,
  pageSize = 50,
) => {
  return http.get<
    { code: number; data: PaginatedResponse<Message> & { hasMore: boolean } }
  >(`/api/chat/conversations/${conversationId}/messages`, {
    params: { beforeMessageId, pageSize },
  });
};

/**
 * 发送消息（返回流式 URL）
 */
export const getStreamMessageUrl = (
  conversationId: number,
  data: SendMessageRequest,
) => {
  const params = new URLSearchParams();
  Object.entries(data).forEach(([key, value]) => {
    if (value !== undefined) {
      params.append(key, JSON.stringify(value));
    }
  });
  return `/api/chat/messages/stream?${params.toString()}`;
};

/**
 * 停止生成消息
 */
export const stopMessageGeneration = async (messageId: number) => {
  return http.post<{ code: number; msg: string }>(`/api/chat/messages/${messageId}/stop`);
};

/**
 * 重新生成消息（返回流式 URL）
 */
export const getRegenerateMessageUrl = (
  messageId: number,
  modelId?: string,
) => {
  const params = new URLSearchParams();
  if (modelId) {
    params.append('modelId', modelId);
  }
  return `/api/chat/messages/${messageId}/regenerate?${params.toString()}`;
};

// ==================== 文件管理 ====================

/**
 * 上传文件
 */
export const uploadFile = async (file: File, conversationId?: number) => {
  const formData = new FormData();
  formData.append('file', file);
  if (conversationId) {
    formData.append('conversationId', conversationId.toString());
  }

  return http.post<{ code: number; data: ChatFile }>('/api/chat/files/upload', formData, {
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
}) => {
  return http.get<{ code: number; data: PaginatedResponse<ChatFile> }>('/api/chat/files', {
    params,
  });
};

/**
 * 删除文件
 */
export const deleteFile = async (fileIds: (number | string)[]) => {
  return http.delete<{ code: number; msg: string }>(`/api/chat/files/${fileIds.join(',')}`);
};

// ==================== 用户设置 ====================

/**
 * 获取用户设置
 */
export const fetchUserSettings = async () => {
  return http.get<{ code: number; data: UserSettings }>('/api/chat/settings');
};

/**
 * 更新用户设置
 */
export const updateUserSettings = async (settings: Partial<UserSettings>) => {
  return http.put<{ code: number; msg: string }>('/api/chat/settings', settings);
};
