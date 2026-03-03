/**
 * Chat Header Component
 * 聊天模块头部组件
 */

import React, { useState } from 'react';
import { SearchOutlined, SettingOutlined, UserOutlined, BulbOutlined } from '@ant-design/icons';
import { cn } from '@/utils/cn';
import { useModels } from '../hooks/useChatActions';
import ModelSelector from './ModelSelector';

interface ChatHeaderProps {
  className?: string;
}

const ChatHeader: React.FC<ChatHeaderProps> = ({ className }) => {
  const [searchValue, setSearchValue] = useState('');
  const { currentModelId } = useModels();

  return (
    <header
      className={cn(
        'h-14 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700',
        'flex items-center justify-between px-4 lg:px-6',
        'sticky top-0 z-50',
        className,
      )}
    >
      {/* Logo */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
            <span className="text-white text-lg">🤖</span>
          </div>
          <span className="text-lg font-semibold text-gray-900 dark:text-white hidden sm:block">
            DeepSeek Chat
          </span>
        </div>
      </div>

      {/* Search Bar */}
      <div className="flex-1 max-w-md mx-4">
        <div className="relative">
          <SearchOutlined className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm" />
          <input
            type="text"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder="搜索对话..."
            className={cn(
              'w-full pl-9 pr-4 py-2',
              'bg-gray-100 dark:bg-gray-700',
              'border border-transparent rounded-lg',
              'text-sm text-gray-900 dark:text-white',
              'placeholder:text-gray-500 dark:placeholder:text-gray-400',
              'focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white dark:focus:bg-gray-600',
              'transition-all duration-200',
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
            'p-2 rounded-lg',
            'hover:bg-gray-100 dark:hover:bg-gray-700',
            'text-gray-600 dark:text-gray-300',
            'transition-colors duration-150',
          )}
          title="切换主题"
        >
          <BulbOutlined className="text-lg" />
        </button>

        {/* Settings */}
        <button
          className={cn(
            'p-2 rounded-lg',
            'hover:bg-gray-100 dark:hover:bg-gray-700',
            'text-gray-600 dark:text-gray-300',
            'transition-colors duration-150',
          )}
          title="设置"
        >
          <SettingOutlined className="text-lg" />
        </button>

        {/* User Menu */}
        <button
          className={cn(
            'p-2 rounded-lg',
            'hover:bg-gray-100 dark:hover:bg-gray-700',
            'text-gray-600 dark:text-gray-300',
            'transition-colors duration-150',
          )}
          title="用户菜单"
        >
          <UserOutlined className="text-lg" />
        </button>
      </div>
    </header>
  );
};

export default ChatHeader;
