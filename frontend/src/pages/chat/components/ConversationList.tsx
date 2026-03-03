/**
 * Conversation List Component
 * 会话列表组件
 */

import React from 'react';
import { PushpinOutlined, MoreOutlined } from '@ant-design/icons';
import { cn } from '@/utils/cn';
import { formatDate } from '@/utils/date';
import type { Conversation } from '../types';

interface ConversationListProps {
  conversations: Conversation[];
  currentConversationId: number | null;
  onConversationClick: (conversationId: number) => void;
}

const ConversationList: React.FC<ConversationListProps> = ({
  conversations,
  currentConversationId,
  onConversationClick,
}) => {
  return (
    <div className="space-y-0.5 px-2">
      {conversations.map((conversation) => (
        <ConversationItem
          key={conversation.conversationId}
          conversation={conversation}
          isActive={conversation.conversationId === currentConversationId}
          onClick={() => onConversationClick(conversation.conversationId)}
        />
      ))}
    </div>
  );
};

interface ConversationItemProps {
  conversation: Conversation;
  isActive: boolean;
  onClick: () => void;
}

const ConversationItem: React.FC<ConversationItemProps> = ({ conversation, isActive, onClick }) => {
  const [showActions, setShowActions] = React.useState(false);

  return (
    <div
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
      className={cn(
        'group relative',
        'px-3 py-2.5 rounded-lg',
        'cursor-pointer',
        'transition-all duration-150',
        isActive
          ? 'bg-indigo-50 dark:bg-indigo-900/20'
          : 'hover:bg-gray-200 dark:hover:bg-gray-800',
      )}
      onClick={onClick}
    >
      <div className="flex items-start space-x-3">
        {/* Left Icon/Avatar */}
        <div className="shrink-0">
          {conversation.isPinned ? (
            <PushpinOutlined className="text-indigo-500 text-sm mt-1" />
          ) : (
            <div className="w-6 h-6 bg-gray-400 dark:bg-gray-500 rounded flex items-center justify-center">
              <span className="text-white text-xs">💬</span>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Title */}
          <div
            className={cn(
              'text-sm font-medium truncate mb-0.5',
              isActive
                ? 'text-indigo-600 dark:text-indigo-400'
                : 'text-gray-900 dark:text-white',
            )}
          >
            {conversation.title}
          </div>

          {/* Meta Info */}
          <div className="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
            <span>{formatDate(conversation.updateTime)}</span>
            <span>·</span>
            <span>{conversation.messageCount} 条消息</span>
          </div>

          {/* Tags */}
          {Array.isArray(conversation.tagList) && conversation.tagList.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {conversation.tagList.slice(0, 2).map((tag) => (
                <span
                  key={tag}
                  className={cn(
                    'inline-flex items-center px-2 py-0.5 rounded',
                    'bg-gray-200 dark:bg-gray-700',
                    'text-xs text-gray-600 dark:text-gray-300',
                  )}
                >
                  {tag}
                </span>
              ))}
              {conversation.tagList.length > 2 && (
                <span className="text-xs text-gray-400">+{conversation.tagList.length - 2}</span>
              )}
            </div>
          )}
        </div>

        {/* Actions */}
        {(showActions || isActive) && (
          <button
            className={cn(
              'shrink-0 p-1 rounded',
              'hover:bg-gray-300 dark:hover:bg-gray-700',
              'text-gray-500 dark:text-gray-400',
              'transition-colors duration-150',
              'opacity-0 group-hover:opacity-100',
              isActive && 'opacity-100',
            )}
            onClick={(e) => {
              e.stopPropagation();
              // TODO: Show actions menu
            }}
          >
            <MoreOutlined className="text-xs" />
          </button>
        )}
      </div>
    </div>
  );
};

export default ConversationList;
