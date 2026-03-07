/**
 * Message List Component - 新拟物风格
 * 消息列表组件
 */

import React from 'react';
import { ClockCircleOutlined, CopyOutlined, ReloadOutlined, DeleteOutlined } from '@ant-design/icons';
import { cn } from '@/utils/cn';
import MarkdownRenderer from './MarkdownRenderer';
import type { Message } from '../types';

interface MessageListProps {
  messages: Message[];
  streamingMessage?: Message;
  isStreaming?: boolean;
}

const MessageList: React.FC<MessageListProps> = ({
  messages,
  streamingMessage,
  isStreaming = false,
}) => {
  // 合并所有消息（包括正在流式生成的消息）
  const allMessages = streamingMessage
    ? [...messages, streamingMessage]
    : messages;

  return (
    <div className="space-y-4 px-6 py-6">
      {allMessages.map((message, index) => (
        <MessageItem
          key={message.messageId || `streaming-${index}`}
          message={message}
          isStreaming={isStreaming && message.messageId === streamingMessage?.messageId}
        />
      ))}
    </div>
  );
};

interface MessageItemProps {
  message: Message;
  isStreaming?: boolean;
}

const MessageItem: React.FC<MessageItemProps> = ({ message, isStreaming }) => {
  const isUser = message.role === 'user';
  const [copied, setCopied] = React.useState(false);

  // 复制消息内容
  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={cn(
        'group relative flex items-start space-x-3',
        isUser ? 'flex-row-reverse space-x-reverse' : 'flex-row',
        'chat2-animate-fade-in',
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center',
          'chat2-neu-btn',
          isUser ? 'text-soft-text dark:text-soft-text-dark' : 'text-soft-text dark:text-soft-text-dark',
        )}
      >
        <span className="text-sm">{isUser ? '👤' : '🤖'}</span>
      </div>

      {/* Content */}
      <div
        className={cn(
          'flex-1 min-w-0',
          isUser ? 'flex justify-end' : 'flex justify-start',
        )}
      >
        <div
          className={cn(
            'rounded-2xl px-4 py-2.5 max-w-[85%]',
            isUser ? 'chat2-user-message' : 'chat2-ai-message',
            isUser ? 'rounded-tr-sm' : 'rounded-tl-sm',
          )}
        >
          {/* Thinking Process (for reasoner model) */}
          {message.thinkingContent && (
            <ThinkingPanel content={message.thinkingContent} />
          )}

          {/* Message Content */}
          <div className={cn(
            'text-base whitespace-pre-wrap break-words',
            'chat2-text-primary',
          )}>
            {isUser ? (
              <p>{message.content}</p>
            ) : (
              <MarkdownRenderer content={message.content} isStreaming={isStreaming} />
            )}
          </div>

          {/* Meta Info */}
          {!isStreaming && message.tokensUsed && (
            <div
              className={cn(
                'flex items-center justify-between mt-2 pt-2',
                'border-t border-soft-text/10',
              )}
            >
              <div className={cn(
                'flex items-center space-x-2',
                'chat2-text-secondary opacity-60',
              )}>
                <ClockCircleOutlined className="text-xs" />
                <span className="text-xs">
                  {new Date(message.createTime).toLocaleTimeString()}
                </span>
                {message.tokensUsed && (
                  <>
                    <span>·</span>
                    <span className="text-xs">{message.tokensUsed} tokens</span>
                  </>
                )}
              </div>

              {/* Copy Button - Always visible for AI messages */}
              {!isUser && (
                <button
                  onClick={handleCopy}
                  className={cn(
                    'flex items-center space-x-1 px-2 py-1 rounded-lg',
                    'chat2-conversation-item',
                    'text-xs transition-all duration-200',
                    copied && 'bg-soft-accent/20 text-soft-accent',
                  )}
                  title={copied ? '已复制' : '复制'}
                >
                  <CopyOutlined className="text-xs" />
                  <span>{copied ? '已复制' : '复制'}</span>
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Error Indicator */}
      {message.hasError && (
        <div className="absolute -bottom-6 left-0">
          <span className="text-xs text-red-500">生成失败，点击重试</span>
        </div>
      )}
    </div>
  );
};

// Thinking Panel Component
interface ThinkingPanelProps {
  content: string;
}

const ThinkingPanel: React.FC<ThinkingPanelProps> = ({ content }) => {
  const [isExpanded, setIsExpanded] = React.useState(false);

  return (
    <div className="mb-2">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          'flex items-center space-x-2 text-xs',
          'px-3 py-1.5 rounded-xl',
          'chat2-neu-btn',
          'chat2-text-primary',
          'transition-all duration-200',
        )}
      >
        <span>🤔</span>
        <span>深度思考</span>
        <span
          className={cn(
            'transition-transform duration-200',
            isExpanded ? 'rotate-180' : '',
          )}
        >
          ▼
        </span>
      </button>
      {isExpanded && (
        <div
          className={cn(
            'mt-2 p-3 rounded-xl',
            'chat2-ai-message',
          )}
        >
          <MarkdownRenderer content={content} />
        </div>
      )}
    </div>
  );
};

// Action Button Component
interface ActionButtonProps {
  icon: React.ReactNode;
  tooltip: string;
  onClick: () => void;
  active?: boolean;
}

const ActionButton: React.FC<ActionButtonProps> = ({ icon, tooltip, onClick, active }) => {
  return (
    <button
      onClick={onClick}
      className={cn(
        'w-8 h-8',
        'chat2-icon-btn',
        'flex items-center justify-center',
        'text-soft-text dark:text-soft-text-dark',
        active && 'bg-soft-accent/20',
      )}
      title={tooltip}
    >
      {icon}
    </button>
  );
};

export default MessageList;
