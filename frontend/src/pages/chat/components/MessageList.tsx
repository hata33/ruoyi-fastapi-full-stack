/**
 * Message List Component
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
  const [showActions, setShowActions] = React.useState(false);
  const [copied, setCopied] = React.useState(false);

  // 复制消息内容
  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
      className={cn(
        'group relative',
        'flex items-start space-x-3',
        isUser ? 'flex-row-reverse space-x-reverse' : 'flex-row',
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center border',
          isUser
            ? 'bg-gray-200 dark:bg-gray-700 border-gray-300 dark:border-gray-600'
            : 'bg-white dark:bg-gray-600 border-gray-300 dark:border-gray-500',
        )}
      >
        <span className="text-gray-700 dark:text-gray-300 text-sm">{isUser ? '👤' : '🤖'}</span>
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
            'inline-block max-w-[85%] rounded-2xl px-4 py-2.5 border',
            isUser
              ? 'bg-gray-200 dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white rounded-br-sm'
              : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white rounded-bl-sm',
          )}
        >
          {/* Thinking Process (for reasoner model) */}
          {message.thinkingContent && (
            <ThinkingPanel content={message.thinkingContent} />
          )}

          {/* Message Content */}
          {isUser ? (
            <p className="text-sm whitespace-pre-wrap wrap-break-word">{message.content}</p>
          ) : (
            <MarkdownRenderer content={message.content} isStreaming={isStreaming} />
          )}

          {/* Meta Info */}
          {!isStreaming && message.tokensUsed && (
            <div
              className={cn(
                'flex items-center space-x-2 mt-2 pt-2',
                'border-t border-gray-200 dark:border-gray-700',
              )}
            >
              <ClockCircleOutlined className="text-xs opacity-70" />
              <span className="text-xs opacity-70">
                {new Date(message.createTime).toLocaleTimeString()}
              </span>
              {message.tokensUsed && (
                <>
                  <span className="opacity-70">·</span>
                  <span className="text-xs opacity-70">{message.tokensUsed} tokens</span>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      {(showActions || message.hasError) && !isStreaming && (
        <div
          className={cn(
            'absolute top-0 flex items-center space-x-1',
            isUser ? '-left-20' : '-right-20',
            'opacity-0 group-hover:opacity-100 transition-opacity duration-200',
          )}
        >
          <ActionButton
            icon={<CopyOutlined />}
            tooltip="复制"
            onClick={handleCopy}
            active={copied}
          />
          {!isUser && (
            <ActionButton
              icon={<ReloadOutlined />}
              tooltip="重新生成"
              onClick={() => {
                /* TODO: Implement regenerate */
              }}
            />
          )}
          <ActionButton
            icon={<DeleteOutlined />}
            tooltip="删除"
            onClick={() => {
              /* TODO: Implement delete */
            }}
          />
        </div>
      )}

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
          'px-2 py-1 rounded',
          'bg-gray-200 dark:bg-gray-600',
          'text-gray-700 dark:text-gray-300',
          'hover:bg-gray-300 dark:hover:bg-gray-500',
          'transition-colors duration-150',
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
            'mt-2 p-2 rounded-lg',
            'bg-white dark:bg-gray-800',
            'text-xs',
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
        'p-1.5 rounded',
        'hover:bg-gray-200 dark:hover:bg-gray-700',
        'text-gray-500 dark:text-gray-400',
        'transition-colors duration-150',
        active && 'bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-400',
      )}
      title={tooltip}
    >
      {icon}
    </button>
  );
};

export default MessageList;
