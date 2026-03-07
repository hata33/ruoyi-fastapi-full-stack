/**
 * Chat2 Area Component - 新拟物风格
 * 聊天主区域组件
 */

import React, { useEffect, useCallback, useRef } from 'react';
import { ArrowLeftOutlined, MoreOutlined, ExportOutlined, TagOutlined } from '@ant-design/icons';
import { cn } from '@/utils/cn';
import { useChatStore } from '../store/chatStore';
import { useMessages, useConversations, useChatUI } from '../hooks/useChatActions';
import MessageList from './MessageList';
import InputArea from './InputArea';
import StopGenerationButton from './StopGenerationButton';
import type { SendMessageRequest } from '../types';

interface ChatAreaProps {
  className?: string;
}

const ChatArea: React.FC<ChatAreaProps> = ({ className }) => {
  const currentConversationId = useChatStore((state) => state.currentConversationId);
  const messages = useChatStore((state) => state.messages);
  const sidebarVisible = useChatStore((state) => state.sidebarVisible);
  const currentModelId = useChatStore((state) => state.currentModelId);

  const { isStreaming, streamingMessage, fetchMessages, stopGeneration, sendMessage } = useMessages();
  const { setSidebarVisible } = useChatUI();
  const { createConversation, setCurrentConversation } = useConversations();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [hasLoadedMessages, setHasLoadedMessages] = React.useState<Record<string, boolean>>({});

  // 加载当前会话的消息（仅在首次加载时）
  useEffect(() => {
    if (currentConversationId && !hasLoadedMessages[currentConversationId]) {
      fetchMessages(currentConversationId);
      setHasLoadedMessages(prev => ({ ...prev, [currentConversationId]: true }));
    }
  }, [currentConversationId, fetchMessages, hasLoadedMessages]);

  // 自动滚动到底部
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, streamingMessage]);

  // 移动端返回按钮
  const handleBack = useCallback(() => {
    setSidebarVisible(true);
  }, [setSidebarVisible]);

  // 处理发送消息（如果没有会话则自动创建）
  const handleSendMessage = useCallback(async (data: SendMessageRequest) => {
    let conversationId = currentConversationId;

    // 如果没有会话，先创建一个新会话
    if (!conversationId) {
      try {
        const newConversation = await createConversation({
          title: data.content.slice(0, 50) + (data.content.length > 50 ? '...' : ''),
          modelId: data.modelId || 'deepseek-chat',
        });
        if (!newConversation) {
          throw new Error('Failed to create conversation');
        }
        conversationId = newConversation.conversationId;
        setCurrentConversation(conversationId);
      } catch (error) {
        console.error('Failed to create conversation:', error);
        throw error;
      }
    }

    // 发送消息
    await sendMessage({ ...data, conversationId });
  }, [currentConversationId, createConversation, setCurrentConversation, sendMessage]);

  // 处理建议卡片点击（发送预设消息）
  const handleSuggestionClick = useCallback(async (message: string) => {
    await handleSendMessage({
      content: message,
      modelId: currentModelId,
    });
  }, [handleSendMessage, currentModelId]);

  // 当前会话的消息列表
  const currentMessages = currentConversationId
    ? messages[currentConversationId] || []
    : [];

  // 判断是否为移动端
  const isMobile = window.innerWidth < 768;

  return (
    <main
      ref={containerRef}
      className={cn(
        'flex flex-col h-full',
        className,
      )}
    >
      {/* Chat Header (Optional) */}
      {currentConversationId && (
        <div className={cn(
          'flex items-center justify-between px-6 py-4',
          'chat2-header',
        )}>
          <div className="flex items-center space-x-3">
            {/* Back Button (Mobile) */}
            {isMobile && (
              <button
                onClick={handleBack}
                className={cn(
                  'w-8 h-8',
                  'chat2-icon-btn',
                  'flex items-center justify-center',
                  'text-soft-text dark:text-soft-text-dark',
                )}
              >
                <ArrowLeftOutlined className="text-sm" />
              </button>
            )}

            {/* Title */}
            <div>
              <h2 className={cn(
                'text-lg font-medium',
                'chat2-text-primary',
              )}>
                新对话
              </h2>
              <div className={cn(
                'flex items-center space-x-2 text-xs mt-0.5',
                'chat2-text-secondary opacity-70',
              )}>
                <span>{currentMessages.length} 条消息</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-2">
            {/* Export */}
            <button className={cn(
              'w-8 h-8',
              'chat2-icon-btn',
              'flex items-center justify-center',
              'text-soft-text dark:text-soft-text-dark',
            )}>
              <ExportOutlined className="text-sm" />
            </button>

            {/* More */}
            <button className={cn(
              'w-8 h-8',
              'chat2-icon-btn',
              'flex items-center justify-center',
              'text-soft-text dark:text-soft-text-dark',
            )}>
              <MoreOutlined className="text-sm" />
            </button>
          </div>
        </div>
      )}

      {/* Message List */}
      <div className="flex-1 overflow-y-auto">
        {currentConversationId ? (
          <>
            <MessageList
              messages={currentMessages}
              streamingMessage={streamingMessage || undefined}
              isStreaming={isStreaming}
            />
            <div ref={messagesEndRef} />
          </>
        ) : (
          // Welcome Screen
          <div className="flex flex-col items-center justify-center h-full px-4">
            <div className="text-center max-w-md">
              {/* Icon */}
              <div className="text-6xl mb-4">🤖</div>

              {/* Title */}
              <h2 className={cn(
                'text-2xl font-bold mb-2',
                'chat2-text-primary',
              )}>
                开始你的第一次对话
              </h2>

              {/* Description */}
              <p className={cn(
                'mb-8 text-sm leading-relaxed',
                'chat2-text-secondary',
              )}>
                我是一个 AI 助手，可以回答问题、提供信息、参与对话，并协助你完成各种语言任务。
              </p>

              {/* Suggestions */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <SuggestionCard
                  icon="💡"
                  title="随便聊聊"
                  description="日常对话与交流"
                  message="你好，能不能介绍一下你自己？"
                  onClick={handleSuggestionClick}
                />
                <SuggestionCard
                  icon="📝"
                  title="写个代码"
                  description="编程与技术问题"
                  message="请帮我写一个 Python 的快速排序算法"
                  onClick={handleSuggestionClick}
                />
                <SuggestionCard
                  icon="🔍"
                  title="问个问题"
                  description="知识问答与学习"
                  message="什么是量子计算？能否用简单的语言解释一下？"
                  onClick={handleSuggestionClick}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className={cn(
        'border-t border-soft-text/10',
        'bg-transparent',
      )}>
        {isStreaming ? (
          <div className="flex justify-center py-3">
            <StopGenerationButton onStop={stopGeneration} />
          </div>
        ) : (
          <InputArea onSendMessage={handleSendMessage} />
        )}
      </div>
    </main>
  );
};

interface SuggestionCardProps {
  icon: string;
  title: string;
  description: string;
  message?: string;
  onClick?: (message: string) => void;
}

const SuggestionCard: React.FC<SuggestionCardProps> = ({ icon, title, description, message, onClick }) => {
  const handleClick = () => {
    if (onClick && message) {
      onClick(message);
    }
  };

  return (
    <button
      onClick={handleClick}
      className={cn(
        'p-4 rounded-xl',
        'chat2-neu-card',
        'hover:shadow-neu-lg dark:hover:shadow-neu-lg-dark',
        'text-left',
        'transition-all duration-200',
        'chat2-animate-fade-in',
      )}
    >
      <div className="text-2xl mb-2">{icon}</div>
      <div className={cn(
        'text-sm font-medium mb-1',
        'chat2-text-primary',
      )}>
        {title}
      </div>
      <div className={cn(
        'text-xs',
        'chat2-text-secondary opacity-70',
      )}>
        {description}
      </div>
    </button>
  );
};

export default ChatArea;
