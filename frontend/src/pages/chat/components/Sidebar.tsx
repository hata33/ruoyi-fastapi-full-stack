/**
 * Chat Sidebar Component
 * 聊天侧边栏组件
 */

import React, { useEffect, useCallback } from 'react';
import { PlusOutlined, PushpinOutlined, TagOutlined, BarChartOutlined } from '@ant-design/icons';
import { cn } from '@/utils/cn';
import { useChatContext } from '../context/ChatContext';
import { useConversations, useTags, useChatUI } from '../hooks/useChatActions';
import ConversationList from './ConversationList';
import TagList from './TagList';
import StatsPanel from './StatsPanel';

interface SidebarProps {
  className?: string;
}

const Sidebar: React.FC<SidebarProps> = ({ className }) => {
  const { conversations, currentConversationId, sidebarCollapsed, sidebarVisible } = useChatContext();
  const { fetchConversations, createConversation, setCurrentConversation } = useConversations();
  const { tags, fetchTags } = useTags();
  const { setSidebarVisible } = useChatUI();

  // 加载会话列表
  useEffect(() => {
    fetchConversations();
    fetchTags();
  }, [fetchConversations, fetchTags]);

  // 新建会话
  const handleNewChat = useCallback(async () => {
    try {
      const newConversation = await createConversation({
        title: '新对话',
        modelId: 'deepseek-chat',
      });
      if (newConversation) {
        setCurrentConversation(newConversation.conversationId);
      }
    } catch (error: any) {
      console.error('Failed to create conversation:', error);
    }
  }, [createConversation, setCurrentConversation]);

  // 计算统计数据
  const stats = React.useMemo(() => {
    const todayMessages = conversations.reduce((sum, c) => sum + c.messageCount, 0);
    const totalTokens = conversations.reduce((sum, c) => sum + c.totalTokens, 0);
    return {
      todayMessages,
      totalTokens,
      totalConversations: conversations.length,
    };
  }, [conversations]);

  // 置顶的会话
  const pinnedConversations = conversations.filter((c) => c.isPinned);
  const unpinnedConversations = conversations.filter((c) => !c.isPinned);

  // 移动端：点击后关闭侧边栏
  const handleConversationClick = useCallback((conversationId: number) => {
    setCurrentConversation(conversationId);
    if (window.innerWidth < 768) {
      setSidebarVisible(false);
    }
  }, [setCurrentConversation, setSidebarVisible]);

  if (!sidebarVisible) {
    return null;
  }

  return (
    <aside
      className={cn(
        'bg-gray-50 dark:bg-gray-900',
        'border-r border-gray-200 dark:border-gray-700',
        'flex flex-col',
        sidebarCollapsed ? 'w-16' : 'w-72',
        'transition-all duration-300',
        className,
      )}
    >
      {/* New Chat Button */}
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={handleNewChat}
          className={cn(
            'w-full flex items-center justify-center space-x-2',
            'bg-gray-900 dark:bg-gray-100',
            'hover:bg-gray-800 dark:hover:bg-gray-200',
            'text-white dark:text-gray-900',
            'px-4 py-2.5 rounded-lg',
            'font-medium text-sm',
            'transition-colors duration-150',
          )}
        >
          <PlusOutlined className="text-base" />
          {!sidebarCollapsed && <span>新建对话</span>}
        </button>
      </div>

      {/* Conversation List */}
      {!sidebarCollapsed && (
        <div className="flex-1 overflow-y-auto">
          {/* Pinned Conversations */}
          {pinnedConversations.length > 0 && (
            <>
              <div className="px-4 py-2">
                <div className="flex items-center space-x-1.5 text-xs font-medium text-gray-500 dark:text-gray-400">
                  <PushpinOutlined className="text-xs" />
                  <span>置顶</span>
                </div>
              </div>
              <ConversationList
                conversations={pinnedConversations}
                currentConversationId={currentConversationId}
                onConversationClick={handleConversationClick}
              />
            </>
          )}

          {/* Unpinned Conversations */}
          {unpinnedConversations.length > 0 && (
            <>
              {pinnedConversations.length > 0 && (
                <div className="px-4 py-2 mt-2">
                  <div className="text-xs font-medium text-gray-500 dark:text-gray-400">
                    全部对话
                  </div>
                </div>
              )}
              <ConversationList
                conversations={unpinnedConversations}
                currentConversationId={currentConversationId}
                onConversationClick={handleConversationClick}
              />
            </>
          )}

          {/* Empty State */}
          {conversations.length === 0 && (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400">
              <div className="text-4xl mb-2">💬</div>
              <div className="text-sm">暂无对话</div>
              <div className="text-xs mt-1">点击上方按钮开始新对话</div>
            </div>
          )}
        </div>
      )}

      {/* Bottom Section */}
      {!sidebarCollapsed && (
        <div className="border-t border-gray-200 dark:border-gray-700">
          {/* Tags */}
          <div className="px-4 py-2">
            <button
              className={cn(
                'w-full flex items-center space-x-2',
                'px-3 py-2 rounded-lg',
                'hover:bg-gray-200 dark:hover:bg-gray-800',
                'text-gray-700 dark:text-gray-300',
                'text-sm',
                'transition-colors duration-150',
              )}
            >
              <TagOutlined className="text-base" />
              <span className="flex-1 text-left">标签管理</span>
              {tags.length > 0 && (
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {tags.length}
                </span>
              )}
            </button>
          </div>

          {/* Stats */}
          <div className="px-4 pb-3">
            <StatsPanel stats={stats} />
          </div>
        </div>
      )}
    </aside>
  );
};

export default Sidebar;
