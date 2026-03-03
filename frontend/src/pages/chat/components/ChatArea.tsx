/**
 * Chat Area Component
 * 聊天主区域组件
 */

import React, { useEffect, useCallback, useRef } from 'react';
import { ArrowLeftOutlined, MoreOutlined, ExportOutlined, TagOutlined } from '@ant-design/icons';
import { cn } from '@/utils/cn';
import { useChatContext } from '../context/ChatContext';
import { useMessages, useConversations, useChatUI } from '../hooks/useChatActions';
import MessageList from './MessageList';
import InputArea from './InputArea';
import StopGenerationButton from './StopGenerationButton';
import type { SendMessageRequest } from '../types';

interface ChatAreaProps {
  className?: string;
}

const ChatArea: React.FC<ChatAreaProps> = ({ className }) => {
  const { currentConversationId, currentConversation, messages, sidebarVisible, currentModelId } = useChatContext();
  const { isStreaming, streamingMessage, fetchMessages, stopGeneration, sendMessage } = useMessages();
  const { setSidebarVisible } = useChatUI();
  const { createConversation, setCurrentConversation } = useConversations();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // 加载当前会话的消息
  useEffect(() => {
    if (currentConversationId) {
      fetchMessages(currentConversationId);
    }
  }, [currentConversationId, fetchMessages]);

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
        conversationId = newConversation.conversationId;
        setCurrentConversation(conversationId);
      } catch (error) {
        console.error('Failed to create conversation:', error);
        throw error;
      }
    }

    // 发送消息
    return sendMessage({ ...data, conversationId });
  }, [currentConversationId, createConversation, setCurrentConversation, sendMessage]);

  // 处理建议卡片点击（发送预设消息）
  const handleSuggestionClick = useCallback(async (message: string) => {
    await handleSendMessage({
      conversationId: currentConversationId || 0,
      content: message,
      modelId: currentModelId,
    });
  }, [handleSendMessage, currentConversationId, currentModelId]);

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
        'flex flex-col h-full bg-white dark:bg-gray-800',
        className,
      )}
    >
      {/* Chat Header (Optional) */}
      {currentConversation && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            {/* Back Button (Mobile) */}
            {isMobile && (
              <button
                onClick={handleBack}
                className="p-2 -ml-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <ArrowLeftOutlined className="text-gray-600 dark:text-gray-300" />
              </button>
            )}

            {/* Title */}
            <div>
              <h2 className="text-base font-semibold text-gray-900 dark:text-white">
                {currentConversation.title}
              </h2>
              <div className="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                <span>{currentConversation.messageCount} 条消息</span>
                <span>·</span>
                <span>{currentConversation.totalTokens} tokens</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-1">
            {/* Pin Button */}
            {currentConversation.isPinned && (
              <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
                <span className="text-indigo-500">📌</span>
              </button>
            )}

            {/* Tags */}
            {currentConversation.tagList.length > 0 && (
              <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
                <TagOutlined className="text-gray-600 dark:text-gray-300" />
              </button>
            )}

            {/* Export */}
            <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
              <ExportOutlined className="text-gray-600 dark:text-gray-300" />
            </button>

            {/* More */}
            <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
              <MoreOutlined className="text-gray-600 dark:text-gray-300" />
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
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                开始你的第一次对话
              </h2>

              {/* Description */}
              <p className="text-gray-600 dark:text-gray-400 mb-8">
                我是 DeepSeek，一个由深度求索开发的大型语言模型。我可以回答问题、提供信息、参与对话，并协助你完成各种语言任务。
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
      <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
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
        'p-4 rounded-xl border border-gray-200 dark:border-gray-700',
        'bg-gray-50 dark:bg-gray-900',
        'hover:bg-gray-100 dark:hover:bg-gray-800',
        'hover:border-indigo-300 dark:hover:border-indigo-600',
        'text-left',
        'transition-all duration-200',
      )}
    >
      <div className="text-2xl mb-2">{icon}</div>
      <div className="text-sm font-medium text-gray-900 dark:text-white mb-1">
        {title}
      </div>
      <div className="text-xs text-gray-500 dark:text-gray-400">
        {description}
      </div>
    </button>
  );
};

export default ChatArea;
