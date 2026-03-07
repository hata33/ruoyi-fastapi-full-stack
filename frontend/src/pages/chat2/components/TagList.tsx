/**
 * Tag List Component - 新拟物风格
 * 标签列表组件
 */

import React from 'react';
import { TagOutlined } from '@ant-design/icons';
import { cn } from '@/utils/cn';
import type { Tag } from '../types';

interface TagListProps {
  tags: Tag[];
  onTagClick?: (tagId: number) => void;
  className?: string;
}

const TagList: React.FC<TagListProps> = ({ tags, onTagClick, className }) => {
  if (tags.length === 0) {
    return null;
  }

  return (
    <div className={cn('space-y-1', className)}>
      {tags.map((tag) => (
        <TagItem
          key={tag.tagId}
          tag={tag}
          onClick={() => onTagClick?.(tag.tagId)}
        />
      ))}
    </div>
  );
};

interface TagItemProps {
  tag: Tag;
  onClick?: () => void;
}

const TagItem: React.FC<TagItemProps> = ({ tag, onClick }) => {
  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full flex items-center space-x-2',
        'px-3 py-2 rounded-xl',
        'chat2-conversation-item',
        'text-sm',
        'transition-all duration-200',
        'group',
      )}
    >
      {/* Tag Color Indicator */}
      <div
        className={cn(
          'w-3 h-3 rounded-full flex-shrink-0',
          'chat2-neu-btn',
        )}
        style={{ backgroundColor: tag.tagColor || '#6B7280' }}
      />

      {/* Tag Name */}
      <span className={cn(
        'flex-1 text-left truncate',
        'chat2-text-primary',
      )}>{tag.tagName}</span>

      {/* Count Badge */}
      {tag.count !== undefined && tag.count > 0 && (
        <span className={cn(
          'text-xs',
          'chat2-text-secondary opacity-60',
        )}>
          {tag.count}
        </span>
      )}
    </button>
  );
};

export default TagList;
