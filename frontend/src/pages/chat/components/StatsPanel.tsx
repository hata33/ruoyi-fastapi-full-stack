/**
 * Stats Panel Component
 * 数据统计面板组件
 */

import React from 'react';
import { MessageOutlined, FireOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { cn } from '@/utils/cn';

interface StatsPanelProps {
  stats: {
    todayMessages: number;
    totalTokens: number;
    totalConversations: number;
  };
  className?: string;
}

const StatsPanel: React.FC<StatsPanelProps> = ({ stats, className }) => {
  const formatTokens = (tokens: number) => {
    if (tokens >= 1000000) {
      return `${(tokens / 1000000).toFixed(1)}M`;
    }
    if (tokens >= 1000) {
      return `${(tokens / 1000).toFixed(1)}K`;
    }
    return tokens.toString();
  };

  return (
    <div
      className={cn(
        'bg-white dark:bg-gray-800',
        'rounded-lg',
        'p-3',
        'border border-gray-200 dark:border-gray-700',
        className,
      )}
    >
      <div className="space-y-2">
        {/* Today Messages */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-xs text-gray-600 dark:text-gray-400">
            <MessageOutlined className="text-xs" />
            <span>今日消息</span>
          </div>
          <span className="text-xs font-semibold text-gray-900 dark:text-white">
            {stats.todayMessages}
          </span>
        </div>

        {/* Total Tokens */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-xs text-gray-600 dark:text-gray-400">
            <FireOutlined className="text-xs" />
            <span>总 Token</span>
          </div>
          <span className="text-xs font-semibold text-gray-900 dark:text-white">
            {formatTokens(stats.totalTokens)}
          </span>
        </div>

        {/* Total Conversations */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-xs text-gray-600 dark:text-gray-400">
            <ClockCircleOutlined className="text-xs" />
            <span>会话总数</span>
          </div>
          <span className="text-xs font-semibold text-gray-900 dark:text-white">
            {stats.totalConversations}
          </span>
        </div>
      </div>
    </div>
  );
};

export default StatsPanel;
