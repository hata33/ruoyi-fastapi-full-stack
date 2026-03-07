/**
 * Conversation List Component - 新拟物风格
 * 会话列表组件
 */

import React from 'react';
import { PushpinOutlined, MoreOutlined } from '@ant-design/icons';
import { cn } from '@/utils/cn';
import { formatDate } from '@/utils/date';
import type { Conversation } from '../types';

interface ConversationListProps {
  conversations: Conversation[];
  currentConversationId: string | null;
  onConversationClick: (conversationId: string) => void;
}

const ConversationList: React.FC<ConversationListProps> = ({
  conversations,
  currentConversationId,
  onConversationClick,
}) => {
  return (
    <div className="space-y-1">
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
        'px-3 py-2.5',
        'cursor-pointer',
        'transition-all duration-200',
        'chat2-conversation-item',
        isActive && 'active',
      )}
      onClick={onClick}
    >
      <div className="flex items-start space-x-3">
        {/* Left Icon/Avatar */}
        <div className="shrink-0">
          {conversation.isPinned ? (
            <div className={cn(
              'w-6 h-6 rounded-lg',
              'chat2-neu-btn',
              'flex items-center justify-center',
              'text-soft-text dark:text-soft-text-dark',
            )}>
              <PushpinOutlined className="text-xs" />
            </div>
          ) : (
            <div className={cn(
              'w-6 h-6 rounded-lg',
              'chat2-neu-btn',
              'flex items-center justify-center',
              'text-soft-text dark:text-soft-text-dark',
            )}>
              <span className="text-xs">💬</span>
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
                ? 'chat2-text-primary'
                : 'chat2-text-primary opacity-90',
            )}
          >
            {conversation.title}
          </div>

          {/* Meta Info */}
          <div className={cn(
            'flex items-center space-x-2 text-xs',
            'chat2-text-secondary opacity-60',
          )}>
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
                    'inline-flex items-center px-2 py-0.5 rounded-lg',
                    'chat2-neu-btn',
                    'text-xs',
                    'chat2-text-primary opacity-70',
                  )}
                >
                  {tag}
                </span>
              ))}
              {conversation.tagList.length > 2 && (
                <span className={cn(
                  'text-xs',
                  'chat2-text-secondary opacity-50',
                )}>+{conversation.tagList.length - 2}</span>
              )}
            </div>
          )}
        </div>

        {/* Actions */}
        {(showActions || isActive) && (
          <button
            className={cn(
              'shrink-0 w-6 h-6',
              'chat2-neu-btn',
              'flex items-center justify-center',
              'text-soft-text dark:text-soft-text-dark opacity-60',
              'hover:opacity-100',
              'transition-all duration-200',
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
