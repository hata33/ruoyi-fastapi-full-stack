/**
 * Chat Module State Management
 * 聊天模块状态管理
 */

import React, { createContext, useContext, useReducer, useEffect } from 'react';
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
import * as chatApi from '../services/chatApi';

// ==================== State 类型 ====================

interface ChatState {
  // 模型相关
  models: Model[];
  currentModelId: string;
  modelConfig: Record<string, ModelConfig>;

  // 会话相关
  conversations: Conversation[];
  currentConversationId: number | null;
  currentConversation: ConversationDetail | null;
  conversationsLoading: boolean;
  conversationsError: string | null;

  // 消息相关
  messages: Record<number, Message[]>;
  messagesLoading: Record<number, boolean>;
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

// ==================== Action 类型 ====================

type ChatAction =
  // 模型相关
  | { type: 'SET_MODELS'; payload: Model[] }
  | { type: 'SET_CURRENT_MODEL'; payload: string }
  | { type: 'SET_MODEL_CONFIG'; payload: { modelId: string; config: ModelConfig } }

  // 会话相关
  | { type: 'SET_CONVERSATIONS'; payload: Conversation[] }
  | { type: 'ADD_CONVERSATION'; payload: Conversation }
  | { type: 'UPDATE_CONVERSATION'; payload: Conversation }
  | { type: 'REMOVE_CONVERSATION'; payload: number[] }
  | { type: 'SET_CURRENT_CONVERSATION'; payload: number | null }
  | { type: 'SET_CURRENT_CONVERSATION_DETAIL'; payload: ConversationDetail | null }
  | { type: 'SET_CONVERSATIONS_LOADING'; payload: boolean }
  | { type: 'SET_CONVERSATIONS_ERROR'; payload: string | null }

  // 消息相关
  | { type: 'SET_MESSAGES'; payload: { conversationId: number; messages: Message[] } }
  | { type: 'ADD_MESSAGE'; payload: { conversationId: number; message: Message } }
  | { type: 'UPDATE_MESSAGE'; payload: { conversationId: number; message: Message } }
  | { type: 'REMOVE_MESSAGE'; payload: { conversationId: number; messageId: number } }
  | { type: 'SET_MESSAGES_LOADING'; payload: { conversationId: number; loading: boolean } }
  | { type: 'SET_STREAMING_MESSAGE'; payload: Message | null }
  | { type: 'SET_IS_STREAMING'; payload: boolean }
  | { type: 'APPEND_STREAMING_CONTENT'; payload: string }
  | { type: 'APPEND_THINKING_CONTENT'; payload: string }

  // 标签相关
  | { type: 'SET_TAGS'; payload: Tag[] }
  | { type: 'ADD_TAG'; payload: Tag }
  | { type: 'REMOVE_TAG'; payload: number[] }

  // 文件相关
  | { type: 'SET_FILES'; payload: ChatFile[] }
  | { type: 'ADD_FILE'; payload: ChatFile }
  | { type: 'REMOVE_FILE'; payload: number[] }

  // 用户设置
  | { type: 'SET_USER_SETTINGS'; payload: UserSettings | null }

  // UI 状态
  | { type: 'ADD_TOAST'; payload: Toast }
  | { type: 'REMOVE_TOAST'; payload: string }
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'SET_SIDEBAR_VISIBLE'; payload: boolean };

// ==================== Reducer ====================

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

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    // 模型相关
    case 'SET_MODELS':
      return { ...state, models: action.payload };
    case 'SET_CURRENT_MODEL':
      return { ...state, currentModelId: action.payload };
    case 'SET_MODEL_CONFIG':
      return {
        ...state,
        modelConfig: {
          ...state.modelConfig,
          [action.payload.modelId]: action.payload.config,
        },
      };

    // 会话相关
    case 'SET_CONVERSATIONS':
      return { ...state, conversations: action.payload };
    case 'ADD_CONVERSATION':
      return { ...state, conversations: [action.payload, ...state.conversations] };
    case 'UPDATE_CONVERSATION':
      return {
        ...state,
        conversations: state.conversations.map((c) =>
          c.conversationId === action.payload.conversationId ? action.payload : c,
        ),
      };
    case 'REMOVE_CONVERSATION':
      return {
        ...state,
        conversations: state.conversations.filter(
          (c) => !action.payload.includes(c.conversationId),
        ),
      };
    case 'SET_CURRENT_CONVERSATION':
      return { ...state, currentConversationId: action.payload };
    case 'SET_CURRENT_CONVERSATION_DETAIL':
      return { ...state, currentConversation: action.payload };
    case 'SET_CONVERSATIONS_LOADING':
      return { ...state, conversationsLoading: action.payload };
    case 'SET_CONVERSATIONS_ERROR':
      return { ...state, conversationsError: action.payload };

    // 消息相关
    case 'SET_MESSAGES':
      return {
        ...state,
        messages: {
          ...state.messages,
          [action.payload.conversationId]: action.payload.messages,
        },
      };
    case 'ADD_MESSAGE':
      return {
        ...state,
        messages: {
          ...state.messages,
          [action.payload.conversationId]: [
            ...(state.messages[action.payload.conversationId] || []),
            action.payload.message,
          ],
        },
      };
    case 'UPDATE_MESSAGE':
      return {
        ...state,
        messages: {
          ...state.messages,
          [action.payload.conversationId]: (
            state.messages[action.payload.conversationId] || []
          ).map((m) =>
            m.messageId === action.payload.message.messageId
              ? action.payload.message
              : m,
          ),
        },
      };
    case 'REMOVE_MESSAGE':
      return {
        ...state,
        messages: {
          ...state.messages,
          [action.payload.conversationId]: (
            state.messages[action.payload.conversationId] || []
          ).filter((m) => m.messageId !== action.payload.messageId),
        },
      };
    case 'SET_MESSAGES_LOADING':
      return {
        ...state,
        messagesLoading: {
          ...state.messagesLoading,
          [action.payload.conversationId]: action.payload.loading,
        },
      };
    case 'SET_STREAMING_MESSAGE':
      return { ...state, streamingMessage: action.payload };
    case 'SET_IS_STREAMING':
      return { ...state, isStreaming: action.payload };
    case 'APPEND_STREAMING_CONTENT':
      return {
        ...state,
        streamingMessage: state.streamingMessage
          ? {
              ...state.streamingMessage,
              content: state.streamingMessage.content + action.payload,
            }
          : null,
      };
    case 'APPEND_THINKING_CONTENT':
      return {
        ...state,
        streamingMessage: state.streamingMessage
          ? {
              ...state.streamingMessage,
              thinkingContent:
                (state.streamingMessage.thinkingContent || '') + action.payload,
            }
          : null,
      };

    // 标签相关
    case 'SET_TAGS':
      return { ...state, tags: action.payload };
    case 'ADD_TAG':
      return { ...state, tags: [...state.tags, action.payload] };
    case 'REMOVE_TAG':
      return {
        ...state,
        tags: state.tags.filter((t) => !action.payload.includes(t.tagId)),
      };

    // 文件相关
    case 'SET_FILES':
      return { ...state, files: action.payload };
    case 'ADD_FILE':
      return { ...state, files: [...state.files, action.payload] };
    case 'REMOVE_FILE':
      return {
        ...state,
        files: state.files.filter((f) => !action.payload.includes(f.fileId)),
      };

    // 用户设置
    case 'SET_USER_SETTINGS':
      return { ...state, userSettings: action.payload };

    // UI 状态
    case 'ADD_TOAST':
      return { ...state, toasts: [...state.toasts, action.payload] };
    case 'REMOVE_TOAST':
      return {
        ...state,
        toasts: state.toasts.filter((t) => t.id !== action.payload),
      };
    case 'TOGGLE_SIDEBAR':
      return { ...state, sidebarCollapsed: !state.sidebarCollapsed };
    case 'SET_SIDEBAR_VISIBLE':
      return { ...state, sidebarVisible: action.payload };

    default:
      return state;
  }
}

// ==================== Context ====================

interface ChatContextValue extends ChatState {
  dispatch: React.Dispatch<ChatAction>;
  // Actions 将通过 hooks 提供
}

const ChatContext = createContext<ChatContextValue | undefined>(undefined);

// ==================== Provider ====================

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  // 初始化数据加载
  useEffect(() => {
    const initializeChat = async () => {
      try {
        // 加载模型列表
        const modelsRes = await chatApi.fetchModels(true);
        if (modelsRes.code === 200 && modelsRes.data) {
          dispatch({ type: 'SET_MODELS', payload: modelsRes.data });
          if (modelsRes.data.length > 0) {
            dispatch({
              type: 'SET_CURRENT_MODEL',
              payload: modelsRes.data[0].modelCode,
            });
          } else {
            // 如果没有启用的模型，设置默认模型
            dispatch({
              type: 'SET_CURRENT_MODEL',
              payload: 'deepseek-chat',
            });
          }
        } else {
          // 没有数据时设置默认模型
          dispatch({ type: 'SET_CURRENT_MODEL', payload: 'deepseek-chat' });
        }
      } catch (error) {
        console.error('Failed to initialize chat:', error);
        // 加载失败时设置默认模型
        dispatch({ type: 'SET_CURRENT_MODEL', payload: 'deepseek-chat' });
      }
    };

    initializeChat();
  }, []);

  return (
    <ChatContext.Provider value={{ ...state, dispatch }}>
      {children}
    </ChatContext.Provider>
  );
};

// ==================== Hooks ====================

export const useChatContext = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatContext must be used within ChatProvider');
  }
  return context;
};
