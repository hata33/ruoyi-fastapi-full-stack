/**
 * Chat Module Custom Hooks
 * 聊天模块自定义 Hooks (使用 Zustand)
 */

import { useCallback } from 'react';
import { useChatStore } from '../store/chatStore';
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
  const conversationsLoading = useChatStore((state) => state.conversationsLoading);
  const conversationsError = useChatStore((state) => state.conversationsError);
  const setConversations = useChatStore((state) => state.setConversations);
  const addConversation = useChatStore((state) => state.addConversation);
  const removeConversation = useChatStore((state) => state.removeConversation);
  const setConversationsLoading = useChatStore((state) => state.setConversationsLoading);
  const setConversationsError = useChatStore((state) => state.setConversationsError);
  const setCurrentConversation = useChatStore((state) => state.setCurrentConversation);

  /** 获取会话列表 */
  const fetchConversations = useCallback(async (params?: Parameters<typeof chatApi.fetchConversations>[0]) => {
    setConversationsLoading(true);
    setConversationsError(null);

    try {
      const res = await chatApi.fetchConversations(params);
      if (res.code === 200) {
        // 后端返回的分页数据，rows 直接在顶层而非 data 中
        const conversations = res.rows || res.data?.rows || [];
        setConversations(conversations);
      } else {
        setConversationsError(res.msg);
      }
    } catch (error: any) {
      setConversationsError(error.message);
    } finally {
      setConversationsLoading(false);
    }
  }, [setConversations, setConversationsLoading, setConversationsError]);

  /** 创建会话 */
  const createConversation = useCallback(async (data: CreateConversationRequest): Promise<Conversation | null> => {
    const res = await chatApi.createConversation(data);
    if (res.code === 200 && res.data) {
      // 处理字段名映射：后端可能返回下划线命名，转换为驼峰命名
      // 使用类型断言来访问后端返回的下划线字段
      const backendData = res.data as any;
      const conversation: Conversation = {
        conversationId: backendData.conversationId || backendData.conversation_id,
        title: backendData.title,
        modelId: backendData.modelId || backendData.model_id,
        isPinned: backendData.isPinned || backendData.is_pinned || false,
        tagList: backendData.tagList || backendData.tag_list || [],
        totalTokens: backendData.totalTokens || backendData.total_tokens || 0,
        messageCount: backendData.messageCount || backendData.message_count || 0,
        createTime: backendData.createTime || backendData.create_time,
        updateTime: backendData.updateTime || backendData.update_time,
      };
      addConversation(conversation);
      return conversation;
    }
    return null;
  }, [addConversation]);

  /** 更新会话 */
  const updateConversation = useCallback(async (data: UpdateConversationRequest) => {
    const res = await chatApi.updateConversation(data);
    if (res.code === 200) {
      await fetchConversations();
    }
    return res.data;
  }, [fetchConversations]);

  /** 删除会话 */
  const deleteConversations = useCallback(async (conversationIds: string[]) => {
    const res = await chatApi.deleteConversation(conversationIds);
    if (res.code === 200) {
      removeConversation(conversationIds);
    }
    return res.data;
  }, [removeConversation]);

  /** 切换置顶 */
  const togglePin = useCallback(async (conversationId: string, isPinned: boolean) => {
    const res = await chatApi.toggleConversationPin(conversationId, isPinned);
    if (res.code === 200) {
      await fetchConversations();
    }
    return res.data;
  }, [fetchConversations]);

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
  const currentConversationId = useChatStore((state) => state.currentConversationId);
  const streamingMessage = useChatStore((state) => state.streamingMessage);
  const isStreaming = useChatStore((state) => state.isStreaming);

  const setMessages = useChatStore((state) => state.setMessages);
  const setMessagesLoading = useChatStore((state) => state.setMessagesLoading);
  const addMessage = useChatStore((state) => state.addMessage);
  const updateMessageId = useChatStore((state) => state.updateMessageId);
  const setStreamingMessage = useChatStore((state) => state.setStreamingMessage);
  const setIsStreaming = useChatStore((state) => state.setIsStreaming);
  const appendStreamingContent = useChatStore((state) => state.appendStreamingContent);
  const appendThinkingContent = useChatStore((state) => state.appendThinkingContent);

  /** 获取消息列表 */
  const fetchMessages = useCallback(async (conversationId: string, beforeMessageId?: string) => {
    setMessagesLoading(conversationId, true);

    try {
      const res = await chatApi.fetchMessages(conversationId, beforeMessageId);
      if (res.code === 200 && res.data) {
        const { rows, hasMore } = res.data;
        setMessages(conversationId, rows);
        return { messages: rows, hasMore };
      }
      return { messages: [], hasMore: false };
    } catch (error) {
      console.error('Failed to fetch messages:', error);
      return { messages: [], hasMore: false };
    } finally {
      setMessagesLoading(conversationId, false);
    }
  }, [setMessages, setMessagesLoading]);

  /** 发送消息（流式） */
  const sendMessage = useCallback(async (data: SendMessageRequest, onEvent?: (event: SSEEvent) => void) => {
    // 优先使用传入的 conversationId，否则使用 store 中的 currentConversationId
    const targetConversationId = data.conversationId || currentConversationId;
    if (!targetConversationId) {
      throw new Error('No current conversation');
    }

    // 生成临时 UUID（用于前端显示，实际ID由后端返回）
    const tempId = `temp-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

    // 先添加用户消息
    const userMessage: Message = {
      messageId: tempId,
      conversationId: targetConversationId,
      role: 'user',
      content: data.content,
      // attachments 现在是 number[]，需要映射为 Attachment 对象
      attachments: data.attachments?.map(fileId => ({
        fileId,
        fileName: '',
        fileType: 'txt',
        fileSize: 0,
        filePath: ''
      })) || [],
      createTime: new Date().toISOString(),
    };
    addMessage(targetConversationId, userMessage);

    // 发起流式请求
    const cancelStream = chatApi.sendMessageStream(
      { ...data, conversationId: targetConversationId },
      (event) => {
        // 从 store 中获取最新的 streamingMessage，避免闭包陷阱
        const currentStreamingMessage = useChatStore.getState().streamingMessage;

        // 处理 SSE 事件
        switch (event.type) {
          case 'message_start':
            // 更新临时用户消息ID为后端返回的实际ID
            updateMessageId(
              targetConversationId,
              tempId,
              event.data.userMessageId,
            );
            // 设置流式AI消息
            setStreamingMessage({
              messageId: event.data.assistantMessageId,  // 使用 assistantMessageId
              conversationId: event.data.conversationId,   // 使用后端返回的 conversationId
              role: 'assistant',
              content: '',
              attachments: [],
              createTime: new Date().toISOString(),
              isStreaming: true,
            } as Message);
            setIsStreaming(true);
            break;

          case 'content_delta':
            appendStreamingContent(event.data.content);
            break;

          case 'thinking_start':
            // 使用最新的 streamingMessage
            const thinkingMsg = useChatStore.getState().streamingMessage;
            if (thinkingMsg) {
              setStreamingMessage({ ...thinkingMsg, thinkingContent: '' });
            }
            break;

          case 'thinking_delta':
            appendThinkingContent(event.data.content);
            break;

          case 'thinking_end':
            break;

          case 'message_end':
            // 使用最新的 streamingMessage，避免闭包陷阱导致消息丢失
            const finalMessage = useChatStore.getState().streamingMessage;
            if (finalMessage && targetConversationId) {
              const completedMessage: Message = {
                ...finalMessage,
                content: finalMessage.content,
                tokensUsed: event.data.tokensUsed,
                isStreaming: false,
              };
              addMessage(targetConversationId, completedMessage);
            }
            setStreamingMessage(null);
            setIsStreaming(false);
            break;

          case 'error':
            console.error('SSE Error:', event.data);
            const errorMsg = useChatStore.getState().streamingMessage;
            if (errorMsg) {
              setStreamingMessage({ ...errorMsg, hasError: true });
            }
            setIsStreaming(false);
            break;
        }

        onEvent?.(event);
      },
      (error) => {
        console.error('Stream error:', error);
        setIsStreaming(false);
      },
      () => {
        // Stream completed
        console.log('Stream completed');
      }
    );

    return cancelStream;
  }, [currentConversationId, addMessage, updateMessageId, setStreamingMessage, setIsStreaming, appendStreamingContent, appendThinkingContent]);

  /** 停止生成 */
  const stopGeneration = useCallback(async () => {
    // 从 store 中获取最新的 streamingMessage，避免闭包陷阱
    const currentStreamingMessage = useChatStore.getState().streamingMessage;
    if (currentStreamingMessage) {
      try {
        await chatApi.stopMessageGeneration(currentStreamingMessage.messageId);
      } catch (error) {
        console.error('Failed to stop generation:', error);
      }
    }
    setIsStreaming(false);
    setStreamingMessage(null);
  }, [setIsStreaming, setStreamingMessage]);

  /** 重新生成 */
  const regenerate = useCallback(async (messageId: string, modelId?: string) => {
    const cancelStream = chatApi.regenerateMessageStream(
      messageId,
      modelId,
      (event) => {
        // 处理 SSE 事件
        switch (event.type) {
          case 'message_start':
            setStreamingMessage({
              messageId: event.data.assistantMessageId,  // 使用 assistantMessageId
              conversationId: event.data.conversationId,   // 使用后端返回的 conversationId
              role: 'assistant',
              content: '',
              attachments: [],
              createTime: new Date().toISOString(),
              isStreaming: true,
            } as Message);
            setIsStreaming(true);
            break;

          case 'content_delta':
            appendStreamingContent(event.data.content);
            break;

          case 'message_end':
            // 使用最新的 streamingMessage，避免闭包陷阱导致消息丢失
            const finalMessage = useChatStore.getState().streamingMessage;
            if (finalMessage && currentConversationId) {
              const completedMessage: Message = {
                ...finalMessage,
                content: finalMessage.content,
                tokensUsed: event.data.tokensUsed,
                isStreaming: false,
              };
              addMessage(currentConversationId, completedMessage);
            }
            setStreamingMessage(null);
            setIsStreaming(false);
            break;

          case 'error':
            console.error('SSE Error:', event.data);
            setIsStreaming(false);
            break;
        }
      },
      (error) => {
        console.error('Regenerate stream error:', error);
        setIsStreaming(false);
      }
    );

    return cancelStream;
  }, [currentConversationId, addMessage, setStreamingMessage, setIsStreaming, appendStreamingContent]);

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
  const tags = useChatStore((state) => state.tags);
  const setTags = useChatStore((state) => state.setTags);
  const addTag = useChatStore((state) => state.addTag);
  const removeTag = useChatStore((state) => state.removeTag);

  /** 获取标签列表 */
  const fetchTags = useCallback(async () => {
    try {
      const res = await chatApi.fetchTags();
      if (res.code === 200 && res.data) {
        setTags(res.data);
      }
    } catch (error) {
      console.error('Failed to fetch tags:', error);
    }
  }, [setTags]);

  /** 创建标签 */
  const createTag = useCallback(async (tagName: string, tagColor?: string) => {
    const res = await chatApi.createTag(tagName, tagColor);
    if (res.code === 200 && res.data) {
      addTag(res.data);
      return res.data;
    }
    throw new Error(res.msg);
  }, [addTag]);

  /** 删除标签 */
  const deleteTags = useCallback(async (tagIds: string[]) => {
    const res = await chatApi.deleteTag(tagIds);
    if (res.code === 200) {
      removeTag(tagIds);
    }
    return res.data;
  }, [removeTag]);

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
  const models = useChatStore((state) => state.models);
  const currentModelId = useChatStore((state) => state.currentModelId);
  const modelConfig = useChatStore((state) => state.modelConfig);
  const setCurrentModel = useChatStore((state) => state.setCurrentModel);
  const setModelConfig = useChatStore((state) => state.setModelConfig);

  /** 获取模型配置 */
  const fetchModelConfig = useCallback(async (modelId: string) => {
    try {
      const res = await chatApi.fetchModelConfig(modelId);
      if (res.code === 200 && res.data) {
        setModelConfig(modelId, res.data);
        return res.data;
      }
    } catch (error) {
      console.error('Failed to fetch model config:', error);
    }
  }, [setModelConfig]);

  /** 保存模型配置 */
  const saveModelConfig = useCallback(async (config: ModelConfig) => {
    const res = await chatApi.saveModelConfig(config);
    if (res.code === 200) {
      setModelConfig(config.modelId, config);
    }
    return res.data;
  }, [setModelConfig]);

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
  const toasts = useChatStore((state) => state.toasts);
  const sidebarCollapsed = useChatStore((state) => state.sidebarCollapsed);
  const sidebarVisible = useChatStore((state) => state.sidebarVisible);
  const addToast = useChatStore((state) => state.addToast);
  const removeToast = useChatStore((state) => state.removeToast);
  const toggleSidebar = useChatStore((state) => state.toggleSidebar);
  const setSidebarVisible = useChatStore((state) => state.setSidebarVisible);

  /** 显示 Toast */
  const showToast = useCallback((
    type: 'success' | 'error' | 'warning' | 'info',
    message: string,
    duration = 3000,
  ) => {
    const id = Date.now().toString();
    addToast({ id, type, message, duration });

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
  }, [addToast, removeToast]);

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
