/**
 * Chat2 Header Component - 新拟物风格
 * 聊天模块头部组件
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SearchOutlined, SettingOutlined, UserOutlined, BulbOutlined, HomeOutlined } from '@ant-design/icons';
import { cn } from '@/utils/cn';
import { useModels } from '../hooks/useChatActions';
import ModelSelector from './ModelSelector';

interface ChatHeaderProps {
  className?: string;
}

const ChatHeader: React.FC<ChatHeaderProps> = ({ className }) => {
  const navigate = useNavigate();
  const [searchValue, setSearchValue] = useState('');
  const { currentModelId } = useModels();

  return (
    <header
      className={cn(
        'h-14 chat2-header',
        'flex items-center justify-between px-4 py-3',
        'sticky top-0 z-50',
        className,
      )}
    >
      {/* Logo */}
      <div
        className="flex items-center space-x-3 cursor-pointer"
        onClick={() => navigate('/')}
        title="返回首页"
      >
        <div className={cn(
          'w-9 h-9',
          'chat2-icon-btn',
          'flex items-center justify-center',
          'text-soft-text dark:text-soft-text-dark',
        )}>
          <HomeOutlined className="text-base" />
        </div>
        <div className="flex items-center space-x-2">
          <div className={cn(
            'w-8 h-8',
            'chat2-neu-btn',
            'flex items-center justify-center',
          )}>
            <span className="text-lg">🤖</span>
          </div>
          <span className={cn(
            'text-lg font-medium hidden sm:block',
            'chat2-text-primary',
          )}>
            AI Chat
          </span>
        </div>
      </div>

      {/* Search Bar */}
      <div className="flex-1 max-w-md mx-4">
        <div className="relative">
          <SearchOutlined className={cn(
            'absolute left-3 top-1/2 -translate-y-1/2 text-sm',
            'text-soft-text opacity-60',
          )} />
          <input
            type="text"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder="搜索对话..."
            className={cn(
              'w-full pl-9 pr-4 py-2',
              'chat2-neu-input',
              'text-sm chat2-text-primary',
              'placeholder:opacity-50',
            )}
          />
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center space-x-2">
        {/* Model Selector */}
        <ModelSelector />

        {/* Theme Toggle */}
        <button
          className={cn(
            'w-9 h-9',
            'chat2-icon-btn',
            'flex items-center justify-center',
            'text-soft-text dark:text-soft-text-dark',
          )}
          title="切换主题"
        >
          <BulbOutlined className="text-base" />
        </button>

        {/* Settings */}
        <button
          className={cn(
            'w-9 h-9',
            'chat2-icon-btn',
            'flex items-center justify-center',
            'text-soft-text dark:text-soft-text-dark',
          )}
          title="设置"
        >
          <SettingOutlined className="text-base" />
        </button>

        {/* User Menu */}
        <button
          className={cn(
            'w-9 h-9',
            'chat2-icon-btn',
            'flex items-center justify-center',
            'text-soft-text dark:text-soft-text-dark',
          )}
          title="用户菜单"
        >
          <UserOutlined className="text-base" />
        </button>
      </div>
    </header>
  );
};

export default ChatHeader;
