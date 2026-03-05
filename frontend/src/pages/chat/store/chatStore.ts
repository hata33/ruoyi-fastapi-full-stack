/**
 * Chat Module Zustand Store
 * 聊天模块 Zustand 状态管理
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type {
  Model,
  ModelConfig,
  Conversation,
  ConversationDetail,
  Message,
  Tag,
  ChatFile,
  UserSettings,
  Toast,
} from '../types';

// ==================== State 类型 ====================

interface ChatState {
  // 模型相关
  models: Model[];
  currentModelId: string;
  modelConfig: Record<string, ModelConfig>;

  // 会话相关
  conversations: Conversation[];
  currentConversationId: string | null;
  currentConversation: ConversationDetail | null;
  conversationsLoading: boolean;
  conversationsError: string | null;

  // 消息相关
  messages: Record<string, Message[]>;
  messagesLoading: Record<string, boolean>;
  streamingMessage: Message | null;
  isStreaming: boolean;

  // 标签相关
  tags: Tag[];

  // 文件相关
  files: ChatFile[];

  // 用户设置
  userSettings: UserSettings | null;

  // UI 状态
  toasts: Toast[];
  sidebarCollapsed: boolean;
  sidebarVisible: boolean;
}

// ==================== Actions 类型 ====================

interface ChatActions {
  // 模型相关
  setModels: (models: Model[]) => void;
  setCurrentModel: (modelId: string) => void;
  setModelConfig: (modelId: string, config: ModelConfig) => void;

  // 会话相关
  setConversations: (conversations: Conversation[]) => void;
  addConversation: (conversation: Conversation) => void;
  updateConversation: (conversation: Conversation) => void;
  removeConversation: (conversationIds: string[]) => void;
  setCurrentConversation: (conversationId: string | null) => void;
  setCurrentConversationDetail: (detail: ConversationDetail | null) => void;
  setConversationsLoading: (loading: boolean) => void;
  setConversationsError: (error: string | null) => void;

  // 消息相关
  setMessages: (conversationId: string, messages: Message[]) => void;
  addMessage: (conversationId: string, message: Message) => void;
  updateMessage: (conversationId: string, message: Message) => void;
  updateMessageId: (conversationId: string, oldMessageId: string, newMessageId: string) => void;
  removeMessage: (conversationId: string, messageId: string) => void;
  setMessagesLoading: (conversationId: string, loading: boolean) => void;
  setStreamingMessage: (message: Message | null) => void;
  setIsStreaming: (isStreaming: boolean) => void;
  appendStreamingContent: (content: string) => void;
  appendThinkingContent: (content: string) => void;

  // 标签相关
  setTags: (tags: Tag[]) => void;
  addTag: (tag: Tag) => void;
  removeTag: (tagIds: string[]) => void;

  // 文件相关
  setFiles: (files: ChatFile[]) => void;
  addFile: (file: ChatFile) => void;
  removeFile: (fileIds: string[]) => void;

  // 用户设置
  setUserSettings: (settings: UserSettings | null) => void;

  // UI 状态
  addToast: (toast: Toast) => void;
  removeToast: (id: string) => void;
  toggleSidebar: () => void;
  setSidebarVisible: (visible: boolean) => void;

  // 重置
  reset: () => void;
}

// ==================== Initial State ====================

const initialState: ChatState = {
  models: [],
  currentModelId: '',
  modelConfig: {},
  conversations: [],
  currentConversationId: null,
  currentConversation: null,
  conversationsLoading: false,
  conversationsError: null,
  messages: {},
  messagesLoading: {},
  streamingMessage: null,
  isStreaming: false,
  tags: [],
  files: [],
  userSettings: null,
  toasts: [],
  sidebarCollapsed: false,
  sidebarVisible: true,
};

// ==================== Store ====================

type ChatStore = ChatState & ChatActions;

export const useChatStore = create<ChatStore>()(
  devtools(
    (set, get) => ({
      // ==================== Initial State ====================
      ...initialState,

      // ==================== 模型相关 ====================
      setModels: (models) => set({ models }, false, 'setModels'),

      setCurrentModel: (modelId) => set({ currentModelId: modelId }, false, 'setCurrentModel'),

      setModelConfig: (modelId, config) =>
        set(
          (state) => ({
            modelConfig: {
              ...state.modelConfig,
              [modelId]: config,
            },
          }),
          false,
          'setModelConfig',
        ),

      // ==================== 会话相关 ====================
      setConversations: (conversations) => set({ conversations }, false, 'setConversations'),

      addConversation: (conversation) =>
        set(
          (state) => ({
            conversations: [conversation, ...state.conversations],
          }),
          false,
          'addConversation',
        ),

      updateConversation: (conversation) =>
        set(
          (state) => ({
            conversations: state.conversations.map((c) =>
              c.conversationId === conversation.conversationId ? conversation : c,
            ),
          }),
          false,
          'updateConversation',
        ),

      removeConversation: (conversationIds) =>
        set(
          (state) => ({
            conversations: state.conversations.filter(
              (c) => !conversationIds.includes(String(c.conversationId)),
            ),
          }),
          false,
          'removeConversation',
        ),

      setCurrentConversation: (conversationId) =>
        set({ currentConversationId: conversationId }, false, 'setCurrentConversation'),

      setCurrentConversationDetail: (detail) =>
        set({ currentConversation: detail }, false, 'setCurrentConversationDetail'),

      setConversationsLoading: (loading) =>
        set({ conversationsLoading: loading }, false, 'setConversationsLoading'),

      setConversationsError: (error) =>
        set({ conversationsError: error }, false, 'setConversationsError'),

      // ==================== 消息相关 ====================
      setMessages: (conversationId, messages) =>
        set(
          (state) => ({
            messages: {
              ...state.messages,
              [conversationId]: messages,
            },
          }),
          false,
          'setMessages',
        ),

      addMessage: (conversationId, message) =>
        set(
          (state) => ({
            messages: {
              ...state.messages,
              [conversationId]: [...(state.messages[conversationId] || []), message],
            },
          }),
          false,
          'addMessage',
        ),

      updateMessage: (conversationId, message) =>
        set(
          (state) => ({
            messages: {
              ...state.messages,
              [conversationId]: (state.messages[conversationId] || []).map((m) =>
                m.messageId === message.messageId ? message : m,
              ),
            },
          }),
          false,
          'updateMessage',
        ),

      updateMessageId: (conversationId, oldMessageId, newMessageId) =>
        set(
          (state) => ({
            messages: {
              ...state.messages,
              [conversationId]: (state.messages[conversationId] || []).map((m) =>
                m.messageId === oldMessageId ? { ...m, messageId: newMessageId } : m,
              ),
            },
          }),
          false,
          'updateMessageId',
        ),

      removeMessage: (conversationId, messageId) =>
        set(
          (state) => ({
            messages: {
              ...state.messages,
              [conversationId]: (state.messages[conversationId] || []).filter(
                (m) => m.messageId !== messageId,
              ),
            },
          }),
          false,
          'removeMessage',
        ),

      setMessagesLoading: (conversationId, loading) =>
        set(
          (state) => ({
            messagesLoading: {
              ...state.messagesLoading,
              [conversationId]: loading,
            },
          }),
          false,
          'setMessagesLoading',
        ),

      setStreamingMessage: (message) =>
        set({ streamingMessage: message }, false, 'setStreamingMessage'),

      setIsStreaming: (isStreaming) =>
        set({ isStreaming }, false, 'setIsStreaming'),

      appendStreamingContent: (content) =>
        set(
          (state) => ({
            streamingMessage: state.streamingMessage
              ? {
                  ...state.streamingMessage,
                  content: state.streamingMessage.content + content,
                }
              : null,
          }),
          false,
          'appendStreamingContent',
        ),

      appendThinkingContent: (content) =>
        set(
          (state) => ({
            streamingMessage: state.streamingMessage
              ? {
                  ...state.streamingMessage,
                  thinkingContent: (state.streamingMessage.thinkingContent || '') + content,
                }
              : null,
          }),
          false,
          'appendThinkingContent',
        ),

      // ==================== 标签相关 ====================
      setTags: (tags) => set({ tags }, false, 'setTags'),

      addTag: (tag) =>
        set(
          (state) => ({
            tags: [...state.tags, tag],
          }),
          false,
          'addTag',
        ),

      removeTag: (tagIds) =>
        set(
          (state) => ({
            tags: state.tags.filter((t) => !tagIds.includes(String(t.tagId))),
          }),
          false,
          'removeTag',
        ),

      // ==================== 文件相关 ====================
      setFiles: (files) => set({ files }, false, 'setFiles'),

      addFile: (file) =>
        set(
          (state) => ({
            files: [...state.files, file],
          }),
          false,
          'addFile',
        ),

      removeFile: (fileIds) =>
        set(
          (state) => ({
            files: state.files.filter((f) => !fileIds.includes(String(f.fileId))),
          }),
          false,
          'removeFile',
        ),

      // ==================== 用户设置 ====================
      setUserSettings: (settings) =>
        set({ userSettings: settings }, false, 'setUserSettings'),

      // ==================== UI 状态 ====================
      addToast: (toast) =>
        set(
          (state) => ({
            toasts: [...state.toasts, toast],
          }),
          false,
          'addToast',
        ),

      removeToast: (id) =>
        set(
          (state) => ({
            toasts: state.toasts.filter((t) => t.id !== id),
          }),
          false,
          'removeToast',
        ),

      toggleSidebar: () =>
        set(
          (state) => ({
            sidebarCollapsed: !state.sidebarCollapsed,
          }),
          false,
          'toggleSidebar',
        ),

      setSidebarVisible: (visible) =>
        set({ sidebarVisible: visible }, false, 'setSidebarVisible'),

      // ==================== 重置 ====================
      reset: () => set(initialState, false, 'reset'),
    }),
    { name: 'ChatStore' },
  ),
);

// ==================== Selectors ====================

/**
 * 选择当前会话的消息列表
 */
export const useCurrentMessages = () =>
  useChatStore((state) => {
    const cid = state.currentConversationId;
    return cid ? state.messages[cid] || [] : [];
  });

/**
 * 选择当前会话的加载状态
 */
export const useCurrentMessagesLoading = () =>
  useChatStore((state) => {
    const cid = state.currentConversationId;
    return cid ? state.messagesLoading[cid] || false : false;
  });

/**
 * 选择当前模型配置
 */
export const useCurrentModelConfig = () =>
  useChatStore((state) => state.modelConfig[state.currentModelId]);

/**
 * 选择会话列表（按置顶和时间排序）
 */
export const useSortedConversations = () =>
  useChatStore((state) => {
    return [...state.conversations].sort((a, b) => {
      // 置顶的排在前面
      if (a.isPinned && !b.isPinned) return -1;
      if (!a.isPinned && b.isPinned) return 1;
      // 都置顶或都不置顶，按更新时间倒序
      return new Date(b.updateTime).getTime() - new Date(a.updateTime).getTime();
    });
  });
