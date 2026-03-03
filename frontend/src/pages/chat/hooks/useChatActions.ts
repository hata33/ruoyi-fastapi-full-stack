/**
 * Chat Module Custom Hooks
 * 聊天模块自定义 Hooks
 */

import { useCallback } from 'react';
import { useChatContext } from '../context/ChatContext';
import * as chatApi from '../services/chatApi';
import type {
  CreateConversationRequest,
  UpdateConversationRequest,
  SendMessageRequest,
  SSEEvent,
  Message,
  ModelConfig,
  Conversation,
} from '../types';

// ==================== 会话相关 Hooks ====================

/**
 * 会话操作 Hook
 */
export const useConversations = () => {
  const { dispatch, conversationsLoading, conversationsError } = useChatContext();

  /** 获取会话列表 */
  const fetchConversations = useCallback(async (params?: Parameters<typeof chatApi.fetchConversations>[0]) => {
    dispatch({ type: 'SET_CONVERSATIONS_LOADING', payload: true });
    dispatch({ type: 'SET_CONVERSATIONS_ERROR', payload: null });

    try {
      const res = await chatApi.fetchConversations(params);
      if (res.code === 200) {
        // 后端返回的分页数据，rows 直接在顶层而非 data 中
        const conversations = res.rows || res.data?.rows || [];
        dispatch({ type: 'SET_CONVERSATIONS', payload: conversations });
      } else {
        dispatch({ type: 'SET_CONVERSATIONS_ERROR', payload: res.msg });
      }
    } catch (error: any) {
      dispatch({ type: 'SET_CONVERSATIONS_ERROR', payload: error.message });
    } finally {
      dispatch({ type: 'SET_CONVERSATIONS_LOADING', payload: false });
    }
  }, [dispatch]);

  /** 创建会话 */
  const createConversation = useCallback(async (data: CreateConversationRequest): Promise<Conversation | null> => {
    const res = await chatApi.createConversation(data);
    if (res.code === 200 && res.data) {
      // 处理字段名映射：后端可能返回下划线命名，转换为驼峰命名
      const conversation: Conversation = {
        conversationId: res.data.conversationId || res.data.conversation_id,
        title: res.data.title,
        modelId: res.data.modelId || res.data.model_id,
        isPinned: res.data.isPinned || res.data.is_pinned || false,
        tagList: res.data.tagList || res.data.tag_list || [],
        totalTokens: res.data.totalTokens || res.data.total_tokens || 0,
        messageCount: res.data.messageCount || res.data.message_count || 0,
        createTime: res.data.createTime || res.data.create_time,
        updateTime: res.data.updateTime || res.data.update_time,
      };
      dispatch({ type: 'ADD_CONVERSATION', payload: conversation });
      return conversation;
    }
    return null;
  }, [dispatch]);

  /** 更新会话 */
  const updateConversation = useCallback(async (data: UpdateConversationRequest) => {

    const res = await chatApi.updateConversation(data);
    if (res.code === 200) {
      await fetchConversations();
    }
    return res.data;
  }, [dispatch, fetchConversations]);

  /** 删除会话 */
  const deleteConversations = useCallback(async (conversationIds: number[]) => {
    try {
      const res = await chatApi.deleteConversation(conversationIds);
      if (res.code === 200) {
        dispatch({ type: 'REMOVE_CONVERSATION', payload: conversationIds });
      }
      return res.data;
    } catch (error: any) {
      throw error;
    }
  }, [dispatch]);

  /** 切换置顶 */
  const togglePin = useCallback(async (conversationId: number, isPinned: boolean) => {
    try {
      const res = await chatApi.toggleConversationPin(conversationId, isPinned);
      if (res.code === 200) {
        await fetchConversations();
      }
      return res.data;
    } catch (error: any) {
      throw error;
    }
  }, [dispatch, fetchConversations]);

  /** 设置当前会话 */
  const setCurrentConversation = useCallback((conversationId: number | null) => {
    dispatch({ type: 'SET_CURRENT_CONVERSATION', payload: conversationId });
  }, [dispatch]);

  return {
    conversationsLoading,
    conversationsError,
    fetchConversations,
    createConversation,
    updateConversation,
    deleteConversations,
    togglePin,
    setCurrentConversation,
  };
};

// ==================== 消息相关 Hooks ====================

/**
 * 消息操作 Hook
 */
export const useMessages = () => {
  const { dispatch, currentConversationId, streamingMessage, isStreaming } = useChatContext();

  /** 获取消息列表 */
  const fetchMessages = useCallback(async (conversationId: number, beforeMessageId?: number) => {
    dispatch({ type: 'SET_MESSAGES_LOADING', payload: { conversationId, loading: true } });

    try {
      const res = await chatApi.fetchMessages(conversationId, beforeMessageId);
      if (res.code === 200) {
        const { rows, hasMore } = res.data;
        dispatch({
          type: 'SET_MESSAGES',
          payload: { conversationId, messages: rows },
        });
        return { messages: rows, hasMore };
      }
      return { messages: [], hasMore: false };
    } catch (error) {
      console.error('Failed to fetch messages:', error);
      return { messages: [], hasMore: false };
    } finally {
      dispatch({ type: 'SET_MESSAGES_LOADING', payload: { conversationId, loading: false } });
    }
  }, [dispatch]);

  /** 发送消息（流式） */
  const sendMessage = useCallback(async (data: SendMessageRequest, onEvent?: (event: SSEEvent) => void) => {
    // 优先使用传入的 conversationId（注意：0 是有效的 falsy 值），否则使用 context 中的 currentConversationId
    const targetConversationId = data.conversationId != null ? data.conversationId : currentConversationId;
    if (!targetConversationId) {
      throw new Error('No current conversation');
    }

    // 先添加用户消息
    const userMessage: Message = {
      messageId: Date.now(), // 临时 ID
      conversationId: targetConversationId,
      role: 'user',
      content: data.content,
      attachments: data.attachments?.map(a => ({ fileId: a.fileId, fileName: '', fileType: 'txt', fileSize: 0, filePath: '' })) || [],
      userId: 0,
      createTime: new Date().toISOString(),
    };
    dispatch({
      type: 'ADD_MESSAGE',
      payload: { conversationId: targetConversationId, message: userMessage },
    });

    // 发起流式请求
    const cancelStream = chatApi.sendMessageStream(
      { ...data, conversationId: targetConversationId },
      (event) => {
        // 处理 SSE 事件
        switch (event.type) {
          case 'message_start':
            dispatch({
              type: 'SET_STREAMING_MESSAGE',
              payload: {
                messageId: event.data.messageId,
                conversationId: targetConversationId,
                role: 'assistant',
                content: '',
                attachments: [],
                userId: 0,
                createTime: new Date().toISOString(),
                isStreaming: true,
              } as Message,
            });
            dispatch({ type: 'SET_IS_STREAMING', payload: true });
            break;

          case 'content_delta':
            dispatch({ type: 'APPEND_STREAMING_CONTENT', payload: event.data.content });
            break;

          case 'thinking_start':
            if (streamingMessage) {
              dispatch({
                type: 'SET_STREAMING_MESSAGE',
                payload: { ...streamingMessage, thinkingContent: '' },
              });
            }
            break;

          case 'thinking_delta':
            dispatch({ type: 'APPEND_THINKING_CONTENT', payload: event.data.content });
            break;

          case 'thinking_end':
            break;

          case 'message_end':
            if (streamingMessage && targetConversationId) {
              const completedMessage: Message = {
                ...streamingMessage,
                content: streamingMessage.content,
                tokensUsed: event.data.tokensUsed,
                isStreaming: false,
              };
              dispatch({
                type: 'ADD_MESSAGE',
                payload: { conversationId: targetConversationId, message: completedMessage },
              });
            }
            dispatch({ type: 'SET_STREAMING_MESSAGE', payload: null });
            dispatch({ type: 'SET_IS_STREAMING', payload: false });
            break;

          case 'error':
            console.error('SSE Error:', event.data);
            if (streamingMessage) {
              dispatch({
                type: 'SET_STREAMING_MESSAGE',
                payload: { ...streamingMessage, hasError: true },
              });
            }
            dispatch({ type: 'SET_IS_STREAMING', payload: false });
            break;
        }

        onEvent?.(event);
      },
      (error) => {
        console.error('Stream error:', error);
        dispatch({ type: 'SET_IS_STREAMING', payload: false });
      },
      () => {
        // Stream completed
        console.log('Stream completed');
      }
    );

    return cancelStream;
  }, [currentConversationId, dispatch, streamingMessage]);

  /** 停止生成 */
  const stopGeneration = useCallback(async () => {
    if (streamingMessage) {
      try {
        await chatApi.stopMessageGeneration(streamingMessage.messageId);
      } catch (error) {
        console.error('Failed to stop generation:', error);
      }
    }
    dispatch({ type: 'SET_IS_STREAMING', payload: false });
    dispatch({ type: 'SET_STREAMING_MESSAGE', payload: null });
  }, [streamingMessage, dispatch]);

  /** 重新生成 */
  const regenerate = useCallback(async (messageId: number, modelId?: string) => {
    const cancelStream = chatApi.regenerateMessageStream(
      messageId,
      modelId,
      (event) => {
        // 处理 SSE 事件
        switch (event.type) {
          case 'message_start':
            dispatch({
              type: 'SET_STREAMING_MESSAGE',
              payload: {
                messageId: event.data.messageId,
                conversationId: currentConversationId!,
                role: 'assistant',
                content: '',
                attachments: [],
                userId: 0,
                createTime: new Date().toISOString(),
                isStreaming: true,
              } as Message,
            });
            dispatch({ type: 'SET_IS_STREAMING', payload: true });
            break;

          case 'content_delta':
            dispatch({ type: 'APPEND_STREAMING_CONTENT', payload: event.data.content });
            break;

          case 'message_end':
            if (streamingMessage && currentConversationId) {
              const completedMessage: Message = {
                ...streamingMessage,
                content: streamingMessage.content,
                tokensUsed: event.data.tokensUsed,
                isStreaming: false,
              };
              dispatch({
                type: 'ADD_MESSAGE',
                payload: { conversationId: currentConversationId, message: completedMessage },
              });
            }
            dispatch({ type: 'SET_STREAMING_MESSAGE', payload: null });
            dispatch({ type: 'SET_IS_STREAMING', payload: false });
            break;

          case 'error':
            console.error('SSE Error:', event.data);
            dispatch({ type: 'SET_IS_STREAMING', payload: false });
            break;
        }
      },
      (error) => {
        console.error('Regenerate stream error:', error);
        dispatch({ type: 'SET_IS_STREAMING', payload: false });
      }
    );

    return cancelStream;
  }, [currentConversationId, dispatch, streamingMessage]);

  return {
    streamingMessage,
    isStreaming,
    fetchMessages,
    sendMessage,
    stopGeneration,
    regenerate,
  };
};

// ==================== 标签相关 Hooks ====================

/**
 * 标签操作 Hook
 */
export const useTags = () => {
  const { dispatch, tags } = useChatContext();

  /** 获取标签列表 */
  const fetchTags = useCallback(async () => {
    try {
      const res = await chatApi.fetchTags();
      if (res.code === 200) {
        dispatch({ type: 'SET_TAGS', payload: res.data });
      }
    } catch (error) {
      console.error('Failed to fetch tags:', error);
    }
  }, [dispatch]);

  /** 创建标签 */
  const createTag = useCallback(async (tagName: string, tagColor?: string) => {
    try {
      const res = await chatApi.createTag(tagName, tagColor);
      if (res.code === 200) {
        dispatch({ type: 'ADD_TAG', payload: res.data });
        return res.data;
      }
      throw new Error(res.msg);
    } catch (error: any) {
      throw error;
    }
  }, [dispatch]);

  /** 删除标签 */
  const deleteTags = useCallback(async (tagIds: number[]) => {
    try {
      const res = await chatApi.deleteTag(tagIds);
      if (res.code === 200) {
        dispatch({ type: 'REMOVE_TAG', payload: tagIds });
      }
      return res.data;
    } catch (error: any) {
      throw error;
    }
  }, [dispatch]);

  return {
    tags,
    fetchTags,
    createTag,
    deleteTags,
  };
};

// ==================== 模型相关 Hooks ====================

/**
 * 模型操作 Hook
 */
export const useModels = () => {
  const { models, currentModelId, modelConfig, dispatch } = useChatContext();

  /** 设置当前模型 */
  const setCurrentModel = useCallback((modelId: string) => {
    dispatch({ type: 'SET_CURRENT_MODEL', payload: modelId });
  }, [dispatch]);

  /** 获取模型配置 */
  const fetchModelConfig = useCallback(async (modelId: string) => {
    try {
      const res = await chatApi.fetchModelConfig(modelId);
      if (res.code === 200) {
        dispatch({
          type: 'SET_MODEL_CONFIG',
          payload: { modelId, config: res.data },
        });
        return res.data;
      }
    } catch (error) {
      console.error('Failed to fetch model config:', error);
    }
  }, [dispatch]);

  /** 保存模型配置 */
  const saveModelConfig = useCallback(async (config: ModelConfig) => {
    try {
      const res = await chatApi.saveModelConfig(config);
      if (res.code === 200) {
        dispatch({
          type: 'SET_MODEL_CONFIG',
          payload: { modelId: config.modelId, config },
        });
      }
      return res.data;
    } catch (error: any) {
      throw error;
    }
  }, [dispatch]);

  return {
    models,
    currentModelId,
    modelConfig,
    setCurrentModel,
    fetchModelConfig,
    saveModelConfig,
  };
};

// ==================== UI 状态相关 Hooks ====================

/**
 * UI 状态 Hook
 */
export const useChatUI = () => {
  const { toasts, sidebarCollapsed, sidebarVisible, dispatch } = useChatContext();

  /** 显示 Toast */
  const showToast = useCallback((
    type: 'success' | 'error' | 'warning' | 'info',
    message: string,
    duration = 3000,
  ) => {
    const id = Date.now().toString();
    dispatch({
      type: 'ADD_TOAST',
      payload: { id, type, message, duration },
    });

    if (duration > 0) {
      setTimeout(() => {
        dispatch({ type: 'REMOVE_TOAST', payload: id });
      }, duration);
    }
  }, [dispatch]);

  /** 移除 Toast */
  const removeToast = useCallback((id: string) => {
    dispatch({ type: 'REMOVE_TOAST', payload: id });
  }, [dispatch]);

  /** 切换侧边栏 */
  const toggleSidebar = useCallback(() => {
    dispatch({ type: 'TOGGLE_SIDEBAR' });
  }, [dispatch]);

  /** 设置侧边栏可见性 */
  const setSidebarVisible = useCallback((visible: boolean) => {
    dispatch({ type: 'SET_SIDEBAR_VISIBLE', payload: visible });
  }, [dispatch]);

  return {
    toasts,
    sidebarCollapsed,
    sidebarVisible,
    showToast,
    removeToast,
    toggleSidebar,
    setSidebarVisible,
  };
};
