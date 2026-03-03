/**
 * Tag List Component
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
        'px-3 py-2 rounded-lg',
        'hover:bg-gray-200 dark:hover:bg-gray-800',
        'text-gray-700 dark:text-gray-300',
        'text-sm',
        'transition-colors duration-150',
        'group',
      )}
    >
      {/* Tag Color Indicator */}
      <div
        className="w-3 h-3 rounded-full flex-shrink-0"
        style={{ backgroundColor: tag.tagColor || '#6B7280' }}
      />

      {/* Tag Name */}
      <span className="flex-1 text-left truncate">{tag.tagName}</span>

      {/* Count Badge */}
      {tag.count !== undefined && tag.count > 0 && (
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {tag.count}
        </span>
      )}
    </button>
  );
};

export default TagList;
