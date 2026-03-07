/**
 * Stats Panel Component - 新拟物风格
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
        'chat2-neu-card',
        'p-3',
        className,
      )}
    >
      <div className="space-y-2">
        {/* Today Messages */}
        <div className="flex items-center justify-between">
          <div className={cn(
            'flex items-center space-x-2 text-xs',
            'chat2-text-secondary opacity-70',
          )}>
            <MessageOutlined className="text-xs" />
            <span>今日消息</span>
          </div>
          <span className={cn(
            'text-xs font-semibold',
            'chat2-text-primary',
          )}>
            {stats.todayMessages}
          </span>
        </div>

        {/* Total Tokens */}
        <div className="flex items-center justify-between">
          <div className={cn(
            'flex items-center space-x-2 text-xs',
            'chat2-text-secondary opacity-70',
          )}>
            <FireOutlined className="text-xs" />
            <span>总 Token</span>
          </div>
          <span className={cn(
            'text-xs font-semibold',
            'chat2-text-primary',
          )}>
            {formatTokens(stats.totalTokens)}
          </span>
        </div>

        {/* Total Conversations */}
        <div className="flex items-center justify-between">
          <div className={cn(
            'flex items-center space-x-2 text-xs',
            'chat2-text-secondary opacity-70',
          )}>
            <ClockCircleOutlined className="text-xs" />
            <span>会话总数</span>
          </div>
          <span className={cn(
            'text-xs font-semibold',
            'chat2-text-primary',
          )}>
            {stats.totalConversations}
          </span>
        </div>
      </div>
    </div>
  );
};

export default StatsPanel;
